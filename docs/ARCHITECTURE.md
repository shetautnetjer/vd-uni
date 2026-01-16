# Architecture

## Modules
- `src/core/` orchestration, config loading, logging
- `src/downloaders/` site adapters and quality selection
- `src/installers/` dependency install helpers
- `src/updaters/` update checks for tools and site adapters
- `src/utils/` shared helpers

## Data Flow
1. Load config
2. Validate environment
3. Resolve target URL and auth (cookies if required)
4. Select highest quality
5. Download
6. Log results and errors

