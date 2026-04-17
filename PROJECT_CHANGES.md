# Project Changes - KhubSoja Chat Automation Platform

> Document for tracking changes, updates, and modifications to the project.

---

## 📋 Overview

| Field | Value |
|-------|-------|
| **Project** | KhubSoja Chat Automation Platform |
| **Location** | `/mnt/data/wd/10_project/projects/khub_soja_sishir/chatbotkhubsoja` |
| **Last Updated** | 2026-04-17 |

---

## 🚧 In Progress

<!-- Items currently being worked on -->

| # | Change | Description | Priority | Owner |
|---|--------|-------------|----------|-------|
| 1 | | | | |

---

## 📝 Planned / Backlog

<!-- Items scheduled for future work -->

| # | Change | Description | Priority | Target Date |
|---|--------|-------------|----------|-------------|
| 1 | | | | |

---

## ✅ Completed

<!-- Completed changes -->

| # | Change | Description | Completed Date |
|---|--------|-------------|----------------|
| 1 | | | |

---

## 🔄 Active Branches

| Branch | Purpose | Status |
|--------|---------|--------|
| `main` | Production branch | Active |

---

## 📦 Dependencies & External Services

| Service | Purpose | Status |
|---------|---------|--------|
| MySQL 8.4 | Database | ✅ Running |
| Redis 7.4 | Cache/Broker | ✅ Running |
| Celery | Background Workers | ✅ Running |
| Cloudflare Tunnel | Public Access | ⏳ Not configured |

---

## 🐛 Known Issues

| Issue | Description | Severity | Status |
|-------|-------------|----------|--------|
| 1 | **Connection Auto-Reconnect Bug** - When a user manually disconnects a platform connection (e.g., Facebook Page), the OAuth session state is deleted but the connection persists in the database as "disconnected". When user tries to reconnect using OAuth, the `start_oauth` flow creates a new state, but since the old session was deleted, attempting to reconnect fails. The `_get_valid_session` method fails because the state-based session lookup can't find the prior OAuth context. | High | Open |

---

## 📝 Notes

The disconnect bug occurs because:
1. `disconnect_connection()` in `platform_connection_service.py` only clears tokens and sets status to DISCONNECTED
2. OAuth session state (`facebook_oauth_session_store`) is not cleaned up on disconnect
3. When user tries to reconnect, `start_oauth` creates a fresh state, but the old connection record still exists with old metadata
4. The `_upsert_connection` method has upsert logic but the old disconnected status may prevent proper reconnection flow

---

## 📎 References

- [Setup Guide](./SETUP_GUIDE.md)
- [Cloudflare Tunnel Setup](./CLOUDFLARE_TUNNEL_SETUP.md)
- [Technical Report](./TECHNICAL_REPORT.md)

---

*Use this document to track all project modifications. Update regularly.*