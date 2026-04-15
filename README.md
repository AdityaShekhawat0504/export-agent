# Export Agent — AI-Powered Trade Compliance Engine

Export Agent is a backend system that automates export compliance decisions using AI-based classification, historical learning, and rule-based risk evaluation.

---

## Overview

The system processes export shipment data and determines whether a shipment should be approved, blocked, or flagged for review. It combines three core components:

* AI classification for HS codes
* Memory-based learning from previous decisions
* Rule-based compliance checks

---

## Features

### Intelligent Classification

Uses an AI model to classify product descriptions into HS codes. Falls back to a default classification if AI is unavailable.

### Learning Memory System

Stores previous classifications and reuses them for similar products. Tracks usage and improves consistency over time.

### Decision Engine

Combines AI output, memory results, and business rules to make a final decision.

### Risk Handling

* Blocks shipments to sanctioned countries (e.g., IR, KP)
* Flags low-confidence classifications for manual review
* Approves high-confidence cases automatically

---

## Architecture

API (FastAPI)
→ Shipment Service
→ Decision Engine
→ Memory / AI Classifier
→ PostgreSQL Database

---

## Tech Stack

* FastAPI
* PostgreSQL
* SQLAlchemy
* OpenAI API

---

## Example Workflow

1. A shipment request is submitted
2. The system checks if a similar product exists in memory
3. If not found, AI is used to classify the product
4. The result is stored for future use
5. Risk rules are applied
6. A decision is returned

---

## Running the Project

Start the server:

uvicorn app.main:app --reload

---

## Environment Variables

Set your API key:

export OPENAI_API_KEY=your_key_here

---

## Future Improvements

* Advanced risk engine (dual-use goods, sanctions lists)
* Explainable decision layer
* Monitoring dashboard
* Real-time compliance alerts

---

## Vision

To build an intelligent compliance layer for global trade that reduces manual work and improves decision accuracy.

---

## Author

Aditya Singh Shekhawat
