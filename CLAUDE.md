# Measure Killer and The Holy Model

A open source free 2D plataform game of Measure Killer: The external tool of Power BI written in python 

The Story follows the hero Measure Killer in different levels. It was given a mission by its master the Power BI Devolper to find the Holy Model, a perfect model, with refresh time under 5 seconds, no unused measures or columns, many to many relationships.

The enemies are those evil unused measures, column and realtionships, that will attack you with guns.

Features:
- Speech ballons for dialogs
- gun animations
- all terrain is destroyable, and it will depend on the stregth of the gun.
- for enemies to attack you, you must be on their line of site.
- this game is violent, so a lot of blood muhahaha

Extra features:
- Menu: start game, settings, load etc
- Settings, users can select their screen resolution
- Saving the game should be possible and handled following best practices


For the future:
- Boss figths
- Release in Steam for free

## Resources:
Right now they are temporary and I will be adding/editing soon.
Tiles and environment: resources/Tiles
Guns: resources/guns
Characters: resources/characters

## Comments and docstrings

- **Never start a docstring line with `#*`, `#!` or `#?`.** Pylance shows the docstring as the hover tooltip, and a
  marker at the start of a line breaks it. Put a warning in a `#!` comment in the body, under the docstring.
- **Break a line only where a sentence ends**, never in the middle of one. This holds for comments and docstrings.
- **Use simple language.** Short sentences, one idea each. No long paragraphs that are hard to follow: split them or
  cut them.


## Never commit

Claude never commits, under any circumstance, in any repo, even when asked. That covers every command that writes a
commit: `git commit` (`--amend` too), `git merge`, `git rebase`, `git cherry-pick` and `git revert`. Leave every
change uncommitted in the working tree: the user reviews it and commits it.

## Principles

## Use

### Use SOLID principles
• Single Responsibility Principle (SRP): A class should have only one reason to change, meaning it should perform only one clear job.
• Open/Closed Principle (OCP): Software entities should be open for extension but closed for modification. You add new features by writing new code rather than changing old code.
• Liskov Substitution Principle (LSP): Child classes must be able to replace their parent classes without breaking the program.
• Interface Segregation Principle (ISP): Clients should not be forced to depend on methods they do not use. Break large interfaces into smaller, specific ones.
• Dependency Inversion Principle (DIP): High-level modules should depend on abstractions, not on concrete implementations

### Use the YAGNI principle (You are no gonna need it)
• Delay implementation: Never write code or build abstractions today based only on a guess that you might need them in the future.
• Fight over-engineering: Prevent wasted time and bloated code by focusing strictly on present, verified requirements.
• Iterate instead: Build the simplest working solution now and rely on refactoring to add features later when real needs emerge.

### Use the DRY Principle (Dont repeat yourself)
• Single Source of Truth: Business rules, validation checks, and data definitions should live in one place. If the rule changes, you only update it in that single location.
• Knowledge vs. Code: Repeating identical lines of code is fine if they represent different domain concepts. The violation happens when the same business logic is copied across multiple files or modules.
• Origin: Introduced as part of clean code philosophy and applied broadly to source code, database schemas, test plans, and documentation

### Use the KISS principle (Keep it simple, Stupid)
• Readability: Another developer should understand what your code does without tracing through endless layers of abstraction.
• Maintainability: Simpler code has fewer bugs, is easier to test, and is safer to change when requirements shift.
• No over-engineering: You avoid writing complex, multi-layered frameworks or adding "just-in-case" features for problems you do not have yet

