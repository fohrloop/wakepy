"""Inhibitor module which uses gtk_application_inhibit(), and follows the
inhibitor module specification (can be used with the pyinhibitor server).

NOTE: Due to the inhibitor counter, this module should not be executed (via a
forced re-import) more than once."""

from __future__ import annotations

import logging
import threading
import warnings

with warnings.catch_warnings():
    # Ignore the PyGIWarning: Gtk was imported without specifying a version
    # first. This should work on GtK 3 and 4.
    warnings.filterwarnings(action="ignore")
    from gi.repository import Gio, Gtk

logger = logging.getLogger(__name__)
latest_inhibitor_identifier = 0

lock = threading.Lock()


class Inhibitor:
    """Inhibitor which uses GTK, namely the gtk_application_inhibit()

    Docs: https://docs.gtk.org/gtk3/method.Application.inhibit.html
    """

    def __init__(self):
        self.app: Gtk.Application | None = None
        self.cookie: int | None = None

    def start(self, *_) -> None:
        self.app = self._get_app()
        try:

            # Docs: https://lazka.github.io/pgi-docs/#Gtk-4.0/classes/Application.html#Gtk.Application.inhibit
            cookie = self.app.inhibit(
                Gtk.ApplicationWindow(application=self.app),
                Gtk.ApplicationInhibitFlags(8),  # prevent idle
                "wakelock requested (wakepy)",
            )
            if not cookie:
                raise RuntimeError(
                    "Failed to inhibit the system (Gtk.Application.inhibit did not "
                    "return a non-zero cookie)"
                )

            self.cookie = cookie

            # The hold() keeps the app alive even without a window.
            # Basically increments the internal hold count of the application.
            # Docs: https://lazka.github.io/pgi-docs/Gio-2.0/classes/Application.html#Gio.Application.hold
            self.app.hold()

        except Exception as error:
            self.app.quit()
            raise RuntimeError(f"Failed to inhibit the system: {error}")

    def _get_app(self) -> Gtk.Application:
        lock.acquire()
        # NOTE: Cannot register two apps with same applidation_id within the
        # same python process (not even on separate threads)! In addition,
        # quitting the app does not seem to unregister / make it possible to
        # reuse the application_id. Therefore, using unique application_id for
        # each instance.
        global latest_inhibitor_identifier
        latest_inhibitor_identifier += 1
        application_id = f"io.readthedocs.wakepy.inhibitor{latest_inhibitor_identifier}"
        try:
            app = Gtk.Application(
                application_id=application_id,
                flags=Gio.ApplicationFlags.IS_SERVICE | Gio.ApplicationFlags.NON_UNIQUE,
            )

            # Cannot use the inhibit() if the app is not registered first.

            logger.debug("Registering Gtk.Application with id  %s", application_id)
            app.register()
            logger.debug("Registered Gtk.Application with id  %s", application_id)
        except Exception as error:
            raise RuntimeError(
                f"Failed to create or register the Gtk.Application: {error}"
            ) from error
        finally:
            lock.release()

        return app

    def stop(self) -> None:
        if self.cookie:
            self.app.uninhibit(self.cookie)
            self.cookie = None

        # The app.release is the counterpart to app.hold(); decrement the internal
        # hold count of the application.
        self.app.release()
        self.app.quit()
        self.app = None
