# InvestorDNA: Step-by-Step Project Plan (Original Vision)

This document breaks down the workflow for the "InvestorDNA" app into manageable phases, based entirely on your original, streamlined vision. The goal is to mathematically map an investor's text/language-based personality directly to their real-world portfolio returns.

## Phase 1: Preparation & Macro Context
**Goal:** Define the economic weather (Macro State) and gather the raw text and financial data for famous investors.
*   **Step 1.1: Macro State Setup** - Download GDP, Inflation, and VIX data from FRED/yfinance. Group these into simple labels like "Recession," "Expansion," or "High Inflation/Low Growth."
*   **Step 1.2: Text Gathering** - Collect shareholder letters, public speeches, and book excerpts from 6-8 target investors (e.g., Buffett, Soros, Dalio) over the last 15-20 years. 
*   **Step 1.3: Portfolio Data** - Download their historical portfolio returns or 13F filings so we have something to map against.

## Phase 2: Building the GRU Persona (What they SAY, over time)
**Goal:** Use a GRU strictly to analyze how their language choices change depending on the economy.
*   **Input Data:** The Text Corpus + Macro State labels.
*   **Step 2.1: Find an NLP/GRU Model** - Clone a pre-existing GRU sequence model from GitHub that can process text embeddings over time.
*   **Step 2.2: Extract Features** - Score the text (using an LLM or basic NLP) to find risk-attitude keywords for each quarter.
*   **Step 2.3: Train the GRU** - Feed the language sentiment features and the Macro State into the GRU. 
*   **Output:** The GRU generates the "True Persona Score" vector—a brilliant mathematical map of how their risk personality adapts to different economic weathers.

## Phase 3: Factor Fingerprinting (What they literally HELD)
**Goal:** Mathematically measure what their actual portfolio was built of.
*   **Step 3.1: Fama-French Regression** - Take the famous investor's historical portfolio returns during that same time period and run a Fama-French regression against standard market factors.
*   **Output:** The "Factor Fingerprint" (e.g., exactly how much Value, Market Beta, or Quality exposure they had). 

## Phase 4: The Direct Persona-to-Factor Mapping (The Core Engine)
**Goal:** Connect the language-based personality directly to the portfolio math.
*   **Step 4.1: Building the Dictionary** - You mathematically link the output of Phase 2 with Phase 3. 
*   **The Result:** You now have an engine that says: *"When someone's language/risk Persona Vector is [X, Y, Z], their optimal Factor Fingerprint is almost always [Value=A, Quality=B, Risk=C]."*. Note: This completely skips the need for finding "divergence" between their words and actions!

## Phase 5: The User App & Gap Advice (Streamlit)
**Goal:** Build the interface where a normal user gets matched, evaluated, and advised.
*   **Step 5.1: The User Quiz** - Build a short web quiz (Holt-Laury style) that asks behavioral finance questions. This calculates the User's Persona Score.
*   **Step 5.2: Persona Matching** - Compare the User's Score to the library of famous investors. (*"Your responses make you 80% Buffett."*)
*   **Step 5.3: User Portfolio Analysis** - The user uploads their current stocks. The app runs a back-end regression to find the user's current Factor Fingerprint.
*   **Step 5.4: Gap Advice** - The app compares the User's actual portfolio Factor Fingerprint against the mapped Buffett Factor Fingerprint. It detects the gap!
*   **Step 5.5: ETF Recommendation** - The app recommends specific ETFs (e.g., Value ETFs or Low Volatility ETFs) to buy or sell to align their real money with their true personality.
