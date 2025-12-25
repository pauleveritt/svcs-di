# Raw Idea: Keyword Injector

## Feature Description

- Creating a KeywordInjector to extract kwargs functionality from DefaultInjector
- Making DefaultInjector simpler by removing kwargs handling
- KeywordInjector should support both sync and async (ideally async wrapping sync)
- KeywordInjector should be designed as a base for future injectors via helpers
- No backwards compatibility needed
- Move keyword-oriented tests to tests/injectors/test_keyword_injector.py
- No @runtime_checkable in src/svcs_di
- Simple tests ensuring protocol compliance
