# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-16

### Added
- **CORE-01**: Formal SIPL grammar (`grammar/sipl.lark`) with positive and negative test suites.
- **CORE-02**: Typed Pydantic AST models with `SourceSpan` tracking and syntax diagnostics.
- **CORE-03**: SIPL interpreter supporting assignments, sequences, blocks, `if-then-else`, `while-do`, `skip`, and step-limit protection.
- **CORE-05**: Structured JSON CLI (`sipl check`, `sipl parse`, `sipl run`) with deterministic exit codes.
- **CORE-06**: Language-agnostic black-box Conformance Suite (`conformance/*.yaml`).
- **IDE-01 / IDE-02**: VS Code extension with TextMate syntax highlighting, snippets, and CLI diagnostics integration.
- **REL-01..04**: GitHub Actions CI/CD pipelines, PyPI packaging, and `.vsix` release automation.