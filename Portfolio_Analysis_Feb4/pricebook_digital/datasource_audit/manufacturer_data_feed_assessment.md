# Manufacturer Data Feed Assessment

**Prepared for:** Kevin McCarron
**Prepared by:** Matthew Scott
**Date:** February 4, 2026

## 1. Introduction

This document assesses the availability of data feeds and APIs from major HVAC manufacturers, including Trane, American Standard, Daikin, Amana, York, and Champion. The findings are intended to inform the DataSource Process Audit and Automation Assessment for Pricebook Digital.

## 2. Manufacturer Data Availability

Our research indicates a lack of a standardized, industry-wide approach to programmatic access for equipment specifications and pricing. The primary method of data distribution remains through PDF catalogs and partner portals.

| Manufacturer | Data Availability |
| :--- | :--- |
| **Trane** | Offers a "Product Feed" through a signup portal, but the format is unclear. A developer portal exists, but its scope is not public. |
| **American Standard** | Provides a "Product Hub" for partners with product literature, including a "2025 Desk Reference Guide," suggesting document-based data distribution. |
| **Daikin** | Has a well-established Developer Portal and the ONECTA Cloud API, primarily for controlling smart HVAC systems, not for a comprehensive product catalog. |
| **Amana** | Relies on a "Literature Library" with product specifications in PDF format. No evidence of a public API or data feed. |
| **York** (Johnson Controls) | Provides a "Source 1 Product Catalog" in PDF format. No specific, publicly accessible API for York HVAC equipment data. |
| **Champion** (Johnson Controls) | Similar to York, with product information available through their website and in documents. No evidence of a public API. |

## 3. Implications for DataSource Automation

The absence of direct API access from most major manufacturers necessitates a web scraping and data automation strategy to build and maintain a comprehensive HVAC equipment database. This approach will require the use of tools and techniques to handle dynamic web content and extract data from PDF documents.

## 4. Recommendations

Given the current landscape, we recommend the following:

*   **Adopt a DataOps Approach:** Implement an automated pipeline for data extraction, validation, and structuring to ensure data quality and scalability.
*   **Leverage Python Libraries:** Utilize Python libraries such as Requests, BeautifulSoup, and Pandas for web scraping, and PyPDF2 and pdfplumber for PDF data extraction.
*   **Implement Continuous Monitoring:** Establish a system for continuous monitoring of manufacturer websites and data feeds to track updates to specifications and pricing.

By pursuing this strategy, Pricebook Digital can create a valuable and defensible data moat, providing a significant competitive advantage in the HVAC software market.
