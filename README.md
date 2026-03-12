# Multilingual Email Phishing Detection using OSINT and Machine Learning

## Overview

This project addresses the growing threat of email phishing by combining
Open-Source Intelligence (OSINT) tools with machine learning models to
detect phishing emails across multiple languages. It tackles a critical
gap in cybersecurity research: most existing ML-based phishing detectors
are trained exclusively on English data, leaving non-English speakers
more vulnerable.

Published on arXiv — [View Paper](https://arxiv.org/abs/2501.08723)

## Problem Statement

Email phishing remains one of the most widespread cyber threats, used to
steal sensitive information or deploy malicious software. Existing ML
models are predominantly trained on English datasets, limiting their
effectiveness in multilingual environments. This project extends phishing
detection to cover both English and Arabic emails by enriching features
with OSINT-derived network intelligence.

## Methodology

- **Datasets**: Multilingual email datasets (English and Arabic)
- **OSINT Tools Used**:
  - `Nmap` — network scanning and open port discovery
  - `theHarvester` — domain and email reconnaissance
- **Features Extracted**: 17 features including domain names, IP
  addresses, and open ports
- **Classification Algorithms Evaluated**:
  - Random Forest ✅ *(best performer — 97.37% accuracy)*
  - Decision Tree
  - Support Vector Machine (SVM)
  - XGBoost
  - Multinomial Naïve Bayes
- **Evaluation**: Accuracy comparison between baseline models (without
  OSINT features) and OSINT-enhanced models

## Key Results

- Random Forest achieved **97.37% accuracy** on both English and Arabic datasets
- OSINT-enhanced models outperformed baseline models without OSINT features
- Findings demonstrate the viability of multilingual phishing detection
  when OSINT features are incorporated

## Technologies Used

- Python
- Scikit-learn / XGBoost
- Nmap
- theHarvester
- Pandas / NumPy
- Matplotlib / Seaborn

## Citation

If you use this work, please cite:

> "Multilingual Email Phishing Attacks Detection using OSINT and Machine
> Learning," arXiv preprint arXiv:2501.08723, January 2025.
> https://arxiv.org/abs/2501.08723
