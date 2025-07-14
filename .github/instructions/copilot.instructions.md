---
applyTo: '**'
---

# Coding Standards & Preferences

## General Guidelines
- Write clean, readable, and maintainable code
- Use descriptive variable and function names
- Add comments for complex logic
- Follow consistent indentation and formatting
- Keep a markdown log file (e.g., CHANGELOG.md) to track changes and updates
    - Every changes should be documented in the CHANGELOG.md file


## Language-Specific Standards
- **JavaScript/TypeScript**: Use ES6+ features, prefer const/let over var
- **Python**: 
    - Follow PEP 8 style guide
    - Avoid using wildcard imports
    - Use type hints for function signatures
    - Do not use import statements in the middle of a file, always import at the top (except for writing tests)
- **Go**: Follow standard Go formatting and naming conventions

## Architecture & Patterns
- Prefer composition over inheritance
- Use dependency injection where appropriate
- Write testable code with clear separation of concerns
- Follow SOLID principles

## Documentation
- Include README files for all projects
- Document public APIs and interfaces
- Add inline documentation for complex algorithms
- When creating new markdown files, use the following organization:
  - Create files in the `docs/` directory
  - Put the customer/public documentation in docs/
  - Put all the "build" documentation in docs/build/ this includes:
    - Specifications
    - Results of tests
    - Summary of features implementation


## Testing
- Write unit tests for all new functionality
- Aim for high test coverage
- Use descriptive test names that explain the scenario
- Create test files in the tests/ directory - standalone test scripts should be placed in the scripts/ directory

## Security
- Validate all inputs
- Use parameterized queries for database operations
- Never commit secrets or credentials
- Follow principle of least privilege