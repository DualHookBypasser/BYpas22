# Overview

This is a Flask web application that provides cookie validation functionality, particularly designed to work with authentication tokens including JWT tokens and Roblox-style cookies. The application features a dark-themed frontend with a form interface for user interaction.

# Recent Changes

## September 27, 2025
- **Fixed Pending Robux Display**: Updated webhook embed message to show actual pending Robux amount instead of hardcoded '0'
  - Added API call to Roblox transaction-totals endpoint (`https://economy.roblox.com/v2/users/{userId}/transaction-totals`)
  - Enhanced `get_roblox_user_info()` function to fetch and return `pendingRobuxTotal` data
  - Updated Discord embed to display real-time pending Robux information
  - Added proper error handling and fallbacks for pending Robux API calls

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Flask (Python) serving as the main web server
- **Cookie Validation System**: Custom validation logic supporting multiple cookie formats:
  - JWT tokens with expiration checking
  - Roblox .ROBLOSECURITY cookies
  - Standard session/authentication cookies
- **Discord Webhook Integration**: Automated webhook system that sends detailed user information
  - Real-time Roblox account data including username, Robux balance, and pending Robux
  - User authentication status and premium item detection (Korblox/Headless)
  - Rich embed messages with profile pictures and formatted data
- **Roblox API Integration**: Multi-endpoint data fetching system:
  - User authentication via `/v1/users/authenticated`
  - Current Robux balance via `/v1/users/currency`
  - Pending Robux via `/v2/users/{userId}/transaction-totals`
  - Premium status and profile data
- **Security Features**: Base64 decoding, JSON payload parsing, and expiration time validation for JWT tokens

## Frontend Architecture
- **Technology**: Vanilla HTML, CSS, and JavaScript
- **Design Pattern**: Single-page application with a card-based UI
- **Styling**: Dark theme with gradient backgrounds and glassmorphism effects
- **Layout**: Responsive design centered on viewport with form-based interaction

## Application Structure
- **Static File Serving**: Flask serves HTML, CSS, and JavaScript files directly
- **API Design**: RESTful endpoints for cookie validation and processing
- **Error Handling**: Built-in validation for malformed tokens and expired credentials

## Security Considerations
- Cookie format validation using regex patterns
- JWT token structure verification (3-part dot-separated format)
- Expiration time checking against current timestamp
- Support for URL-safe base64 decoding with proper padding

# External Dependencies

## Python Libraries
- **Flask**: Web framework for HTTP server and routing
- **requests**: HTTP client library for external API calls
- **json**: Built-in JSON parsing and manipulation
- **base64**: Encoding/decoding functionality for JWT tokens
- **re**: Regular expression matching for cookie validation
- **time**: Timestamp operations for token expiration checking

## Frontend Dependencies
- **No external frameworks**: Uses vanilla HTML, CSS, and JavaScript
- **Self-contained styling**: All CSS defined inline without external libraries

## Potential Integrations
- **Roblox Platform**: Specific support for .ROBLOSECURITY cookie format
- **JWT Token Systems**: Compatible with standard JWT authentication flows
- **Session Management**: Support for various cookie-based authentication systems