"""Open the full chooser through its normal single-click entry."""
def open_effect_choices(page, selector):
    kind={'#filterBtn':'filters','#templateBtn':'templates','#layoutBtn':'layout'}[selector]
    page.locator(selector).click()
    page.wait_for_function("kind=>sheetKind===kind&&!$('sheet').hidden",arg=kind)
