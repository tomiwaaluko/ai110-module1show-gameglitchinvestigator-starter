# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

When I first ran the game, it looked fine on the surface — there was a text input, a submit button, and a sidebar with difficulty settings. But the moment I opened the "Developer Debug Info" tab to cheat and see the secret number, I noticed it kept changing every single time I clicked Submit. I could never actually win because the target was moving. On top of that, even when I guessed a number that was clearly lower than the secret, the game told me to go lower — the hints were completely backwards. A third thing I caught pretty quickly was that the info bar always said "Guess a number between 1 and 100" even when I switched to Easy mode, which is supposed to be a much smaller range.

---

## 2. How did you use AI as a teammate?

I used Claude (Claude Code) and ChatGPT during this project. For the state bug, I asked ChatGPT "How do I keep a variable from resetting in Streamlit when I click a button?" and it correctly explained that Streamlit reruns the entire script on every interaction, so any variable assigned outside of `st.session_state` gets re-created from scratch. It told me to use `if "secret" not in st.session_state` before assigning the random number, which was exactly right — I verified it by submitting a guess and confirming the debug panel showed the same number. One place where AI steered me slightly wrong was when I asked about the `check_guess` function. It initially suggested I keep the tuple return format `(outcome, message)` for "clean separation of concerns," but the tests in `test_game_logic.py` expected just a plain string like `"Win"` — not a tuple. I had to read the test file myself to catch that mismatch.

---

## 3. Debugging and testing your fixes

I treated each bug as its own mini-experiment: change one thing, run the app or tests, and see if the symptom disappeared. For the hints bug, I manually guessed a number I knew was too high (I had the secret number from the debug panel) and checked whether the message said "Go LOWER" — before my fix it said "Go HIGHER," which was wrong. After flipping the logic in `check_guess`, the correct message appeared. For automated testing I ran `pytest` after moving the logic into `logic_utils.py`, and all three tests passed immediately once the function returned a plain string instead of a tuple. The tests were really helpful because `test_guess_too_high` directly confirmed that passing `60` with a secret of `50` returns `"Too High"` — no ambiguity. Claude helped me understand why the tests were failing initially by pointing out the return type mismatch between the original tuple and what the tests expected.

---

## 4. What did you learn about Streamlit and state?

The secret number kept changing because Streamlit re-executes the entire Python script from top to bottom every time the user interacts with anything — clicking a button, typing in a field, you name it. In the broken code, `random.randint()` was called at the top level with no guard, so a fresh random number got picked on every rerun. Think of Streamlit like a whiteboard that gets completely erased and redrawn every time someone taps it. `st.session_state` is like a sticky note attached to the side of the whiteboard — it survives the erase. To explain it to a friend: imagine your app is a vending machine that resets every time you press a button, but `session_state` is a little memory card that remembers what you already selected. The fix that stabilized the secret number was wrapping the assignment in `if "secret" not in st.session_state`, so the random number only gets picked once at the very start of the game.

---

## 5. Looking ahead: your developer habits

One habit I want to keep is reading the test file before touching any logic. The tests told me exactly what interface `check_guess` needed to have — if I had just refactored blindly without reading them first, I would have kept the tuple return and been confused about why everything was failing. Going forward, I'll treat test files as a spec, not an afterthought. Next time I work with AI on a coding task I'd be more skeptical upfront when AI suggests keeping existing structure "for cleanliness" — in this case the AI's preference for a tuple return was technically reasonable in isolation but flat-out broke the tests. This project made me realize that AI-generated code can look completely plausible and still be subtly, systematically wrong in ways that only show up when you actually run it. You can't just read AI code and trust it; you have to play with it and break it.
