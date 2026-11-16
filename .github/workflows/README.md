# GitHub Engineering Support Workflows

## Overview

This repository contains a collection of GitHub Actions workflows that support the software development lifecycle by automating repetitive quality and security verification tasks.

These workflows are **engineering support tools**, not a standalone repository quality management framework.

Their purpose is to:

- improve development efficiency;
- provide rapid feedback during pull requests;
- automate repeatable verification activities;
- reduce manual engineering effort;
- assist developers in identifying issues early.

The workflows do **not** replace engineering judgement. They provide evidence that helps developers and reviewers make informed decisions throughout the development lifecycle.

---

# Design Principles

The workflows were intentionally designed around several principles.

## Single Responsibility

Each workflow performs one clearly defined engineering activity.

Examples include:

- source code quality verification;
- source code security analysis;
- dependency hygiene validation;
- dependency security assessment;
- dependency regression risk analysis;
- SBOM generation.

Each workflow can evolve independently without affecting the others.

---

## Independent Execution

Workflows are intentionally independent.

A failure in one workflow does not prevent other engineering assessments from being executed unless explicitly required.

This allows developers to receive as much feedback as possible from a single execution.

---

## Engineering Assistance

The workflows provide engineering evidence rather than engineering decisions.

For example:

- static analysis reports;
- dependency vulnerability reports;
- dependency regression analysis;
- SBOM documents;
- pull request summaries.

Developers remain responsible for evaluating the reported information.

---

## Fail Closed

Whenever a workflow cannot complete its assessment correctly, it fails.

Examples include:

- invalid reports;
- corrupted scanner output;
- missing artifacts;
- scanner execution failures.

An incomplete assessment is never interpreted as a successful assessment.

---

## Explicit Risk Acceptance

Some engineering decisions require human judgement.

For example, dependency updates may intentionally introduce acceptable residual risk after review.

The repository therefore supports explicit risk acceptance using the `dependency-risk-approved` pull request label.

The workflows recognise this label as evidence that the dependency changes have been reviewed and approved by the engineering team.

---

# Workflow Overview

## PR Code Quality Gate

Purpose

Maintains source code quality during pull requests.

Checks include:

- Ruff
- Black
- MyPy

The workflow identifies formatting issues, lint violations and type checking problems before code is merged.

---

## PR Code Security Scan

Purpose

Performs static application security testing of Python source code.

Current tool:

- Bandit

The workflow identifies potentially insecure coding practices and reports findings requiring engineering review.

---

## Dependency Hygiene Check

Purpose

Validates dependency declarations.

Current tool:

- Deptry

The workflow detects:

- unused dependencies;
- missing dependencies;
- incorrectly declared dependencies.

Its purpose is to maintain an accurate dependency definition.

---

## Dependency Regression Risk Check

Purpose

Evaluates dependency changes introduced by a pull request.

The workflow compares dependency graphs between the pull request and the repository baseline.

Its goal is not to identify vulnerabilities but to estimate engineering risk introduced by dependency modifications.

If elevated risk is detected, manual review is required.

Once reviewed, engineers may explicitly acknowledge the residual risk by applying the `dependency-risk-approved` label.

---

## Dependency Security Scan

Purpose

Performs vulnerability assessment of project dependencies.

Current tools include:

- Syft
- Trivy
- Grype
- OSV Scanner
- Bomber

Results from multiple scanners are normalised and consolidated to provide a broader vulnerability assessment.

The workflow assists engineers in identifying known vulnerable dependencies before software is released.

---

## SBOM Generation

Purpose

Generates Software Bill of Materials (SBOM) documents.

Supported formats include:

- CycloneDX
- SPDX

The workflow is intended primarily for ad-hoc execution when software inventory documentation is required for engineering, compliance or customer purposes.

---

## Security Pipeline

Purpose

Coordinates dependency-related security workflows.

It orchestrates multiple security assessments while keeping each workflow independently maintainable.

The pipeline itself performs no security analysis.

---

# Engineering Philosophy

The workflows are intended to automate repetitive verification activities while keeping engineering decision making under human control.

Automation performs:

- evidence collection;
- report generation;
- repeated verification;
- consistency checks.

Engineers remain responsible for:

- evaluating findings;
- accepting residual risk;
- selecting remediation strategies;
- approving software changes.

This separation ensures that automation improves development efficiency without replacing engineering judgement.