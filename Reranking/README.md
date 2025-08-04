# Reranking Module

This module performs post-retrieval reranking of candidate documents in the RAG pipeline.

## Purpose

After initial document retrieval, this module applies scoring functions based on features such as:

- Publication year
- Citation count
- Concept relevance score

The goal is to boost relevance and trustworthiness of context documents before passing them to the language model.

## Contents

- `scoring_functions.R`: Functions that assign a relevance score to each document based on weighted feature combinations.
- `ranking_pipeline.R`: Applies scoring to retrieved candidates and returns a reranked list.
- `feature_engineering.R`: Utilities to extract and normalize features from OpenAlex or other metadata.
- `exploration_notebook.qmd`: Quarto notebook for experimenting with scoring strategies and feature weights.
