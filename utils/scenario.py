import pyautogui

def ura():
  race_btn = pyautogui.locateCenterOnScreen("assets/ura/ura_race_btn.png", confidence=0.8, minSearchTime=0.2)
  if race_btn:
    pyautogui.click(race_btn)