def bootPartnerAspect():
    # Conditionally booted Pentacle partner application off-thread.
    # Note: This should work in environments even if server is under autorun shell.
    from pentacle.bus import PENTACLE_PARTNER_NAME_ENV_VAR
    from os import environ
    if environ.get(PENTACLE_PARTNER_NAME_ENV_VAR):
        from pentacle.bus.partners import PartneredApplication
        from pentacle.runtime import nth
        nth(PartneredApplication.Main)
