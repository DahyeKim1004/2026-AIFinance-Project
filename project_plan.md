# InvestorDNA: Step-by-Step Project Plan

This document breaks down the complex workflow of creating the "InvestorDNA" app into manageable, bite-sized phases. The ultimate goal is to generate dynamic personas of famous investors and match users to them to provide personalized portfolio advice.

## Phase 1: Preparation & Macro Context
**Goal:** Define the economic weather (Macro State) so the AI understands *when* decisions were made, and gather the raw data.
*   **Step 1.1: Macro State Setup** - Download GDP, Inflation, and VIX data from FRED/yfinance. Group these into simple labels like "Recession," "Expansion," or "High Inflation/Low Growth."
*   **Step 1.2: 13F Data Gathering** - Download quarterly 13F holdings (from SEC EDGAR) for 6-8 target investors (e.g., Buffett, Soros, Dalio) over the last 15-20 years.
*   **Step 1.3: Text Gathering** - Collect shareholder letters, public speeches, and book excerpts from these same investors.

## Phase 2: Building the "Revealed" Persona (What they DO)
**Goal:** Use a GRU (a sequence AI model) to mathematically represent how each investor trades in different economic states.
*   **Input Data:** 13F Portfolios + Macro State labels.
*   **Step 2.1: Find a GRU Model** - Clone a pre-existing GRU sequence model from GitHub to avoid coding one from scratch.
*   **Step 2.2: Feature Engineering** - From the 13F data, calculate portfolio stats per quarter (e.g., portfolio concentration, turnover rate, sector distribution).
*   **Step 2.3: Train the GRU** - Feed the quarterly stats and Macro State into the GRU. 
*   **Output:** The GRU generates a mathematical vector representing the investor's actual trading behavior over time.

## Phase 3: Building the "Stated" Persona (What they SAY)
**Goal:** Use an LLM to read the investors' words and score their claimed investment personality.
*   **Input Data:** Text documents + The Macro State matching the date of the text.
*   **Step 3.1: Choose the LLM** - Pick either Claude or OpenAI and stick with it to prevent bias.
*   **Step 3.2: LLM Prompting** - Feed the text into the LLM and ask it to rate the investor on distinct behavioral traits: *Loss Aversion (1-10), Risk Preference (1-10), Time Horizon (Short vs. Long).*
*   **Output:** A numerical score of their "Stated" personality traits under different economies.

## Phase 4: Persona Scoring & Factor Fingerprinting
**Goal:** Combine their words and actions into one "True Persona Score" and map that score to actual portfolio math (Factors). 
*   **Step 4.1: The True Persona Score** - mathematically combine the GRU output (Actions) with the LLM output (Words). This handles inconsistencies between talk/action and gives the robust risk attitude profile for that investor.
*   **Step 4.2: Fama-French Regression** - Take the investor's historical returns and run a standard Fama-French regression against market factors (Market, Size, Value, Quality).
*   **Output:** The "Factor Fingerprint" (e.g., exactly how much Value or Quality exposure they have). Now you have a direct mapping table: *True Persona Score* <--> *Factor Fingerprint*.

## Phase 5: The User App & Gap Analysis (Streamlit)
**Goal:** Build the interface where a normal user gets matched, evaluated, and advised.
*   **Step 5.1: The User Quiz** - Build a short web quiz (Holt-Laury style) that asks behavioral finance questions. This calculates the User's Persona Score.
*   **Step 5.2: Persona Matching** - Compare the User's Persona Score to the library of famous investors. (*"Your responses make you 80% Buffett."*)
*   **Step 5.3: User Portfolio Analysis** - The user uploads their current stocks. The app runs a back-end regression to find the user's current Factor Fingerprint.
*   **Step 5.4: Gap Advice** - The app compares the User's Factor Fingerprint with their matched investor's Factor Fingerprint. It detects the gap (e.g., *"You are acting like a high-risk tech investor, but your personality profile says you should be a value investor like Buffett"*).
*   **Step 5.5: ETF Recommendation** - The app recommends specific ETFs (e.g., Value ETFs or Low Volatility ETFs) to buy or sell to close the gap and align their real money with their true personality.
