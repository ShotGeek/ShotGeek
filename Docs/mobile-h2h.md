# Mobile Head-to-Head View

This document describes the structure and styling approach for the mobile-friendly head-to-head comparison page introduced in this commit. The goal is to keep desktop styling intact while providing a touch-optimized layout on phones.

## Components

### PlayerSearchField
- Persistent `<label>` for accessibility
- Input and search button sized to at least 48px high

### PlayerCard
- Implemented as `<article role="region">` with semantic child elements
- Avatar shows a skeleton while loading and falls back to `avatar-silhouette.svg` if the real image fails to load
- Stats rendered as `<dl>` pairs to aid screen readers

### CompareBar
- Sticky bottom bar that respects device safe areas
- Enabled only when both players have been selected

## Tokens & Accessibility
- Colors, radius and elevation defined as CSS variables so the mobile view matches the desktop palette
- Dark mode supported via `prefers-color-scheme`
- Skeleton animation disabled when `prefers-reduced-motion` is set

## Future Work
- Add typeahead search suggestions
- Instrument share actions with analytics
- Expand testing with axe-core or similar a11y tooling
