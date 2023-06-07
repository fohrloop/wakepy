def running():
    """Keep the system running your programs; Prevent system from sleeping /
    suspending automatically. Does not keep display on, and does not prevent
    automatic screen lock or screen saver.

    Example
    -------
    .. code-block::

        from wakepy import keep
        
        with keep.running():
            # Do something that takes a long time but does not need to be
            # displayed.
    
    """

def presenting():
    """Keep the system running your programs and showing some content; Prevent
    screen saver and screen locker from switching on. Implies that system is
    prevented from  sleeping / suspending automatically. 

    Example
    -------
    .. code-block::

        from wakepy import keep
        
        with keep.presenting():
            # Do something that takes a long time and needs
            # to be shown to user; no automatic screen lock

    
    .. warning::

        🔒 Since screen will not be automatically locked, you don't want to leave
        your machine unattended in an insecure place.

    """