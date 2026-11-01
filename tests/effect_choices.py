"""Open the full chooser through the effect browsing controls."""
def open_effect_choices(page, selector):
    kind='filters' if selector=='#filterBtn' else 'templates'
    if page.evaluate('(kind)=>window.EffectBrowser?.kind()===kind',kind):
        if page.locator('#sheet').is_hidden():page.locator('#effectAll').click()
    else:
        page.locator(selector).click()
        if page.locator('#effectAll').is_visible():page.locator('#effectAll').click()
