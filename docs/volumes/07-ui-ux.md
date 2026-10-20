---
volume: 07
title: UI/UX Specification
status: draft
---

# UI/UX Specification

> **SentinelVision AI — Enterprise Documentation Suite**
> Status legend: Implemented | Planned | Future


## 1. Design Principles

- Security-first dark operations theme
- Responsive layout for desktop and mobile browsers
- Clear severity signaling for alerts and events
- Minimize alert fatigue via prioritization and filters
- WCAG 2.1 AA compliance target

## 2. Information Architecture

```
Login -> App Shell
  Overview
  Cameras
  Events
  Alerts
  Reports (Planned)
  Attendance (Planned)
  Visitors (Planned)
  Users (Planned)
  Settings (Planned)
```

## 3. Screen Catalog

| ID | Screen | Status | Description |
|----|--------|--------|-------------|
| UI-LOGIN | Login | Implemented | JWT authentication entry |
| UI-DASH | Dashboard Overview | Implemented | Summary metric cards |
| UI-CAM | Camera Management | Partial | Read-only inventory list |
| UI-LIVE | Live View | Planned | Low-latency stream grid |
| UI-EVT | Event Review | Partial | Review queue with confirm/false+ |
| UI-ALERT | Alerts | Partial | Alert cards with acknowledge |
| UI-RPT | Reports | Planned | Export and schedule reports |
| UI-ATT | Attendance | Planned | Daily attendance dashboard |
| UI-VIS | Visitor Management | Planned | Pre-register and check-in |
| UI-USR | User Management | Planned | Membership and role admin |
| UI-SET | Settings | Planned | Org settings, retention, modules |
| UI-EDGE | Edge Health | Planned | Device status and diagnostics |

## 4. UI-LOGIN

**Purpose:** Authenticate operator and establish JWT session.

**Components:** username field, password field, submit button, error banner, demo hint.

**States:** idle, loading, error, success redirect.

**Wireframe (ASCII):**

```
+-----------------------------+
|      SentinelVision AI      |
|  [ username            ]    |
|  [ password            ]    |
|  [ Sign in ]                |
+-----------------------------+
```

## 5. UI-DASH

**Metrics:** cameras online/total, events today, pending review, open/critical alerts, edge online/total.

**Interaction:** read-only cards; auto-refresh Planned.

## 6. UI-EVT

**Table columns:** time, type, camera, site, severity, confidence, status, actions.

**Actions:** Confirm, False Positive (Operator+).

**Planned:** filters, pagination controls, evidence thumbnail preview.

## 7. Component Library

| Component | Usage |
|-----------|-------|
| MetricCard | Dashboard KPIs |
| DataTable | Cameras, events |
| AlertCard | Alerts list |
| Badge | status/severity |
| SidebarNav | Primary navigation |
| ErrorBanner | API failures |

## 8. Navigation Flow

Login success -> Overview -> Events/Alerts for investigation -> Acknowledge alert -> Optional review confirmation.

## 9. Responsive Behavior

- Desktop: persistent sidebar
- Mobile: stacked sidebar/nav wrap; tables horizontally scrollable

## 10. Accessibility

- Keyboard navigable form controls
- Color contrast >= 4.5:1 for text
- Planned: focus indicators, ARIA labels on tables/buttons

## 11. PWA

Manifest present; service worker and push notifications Planned.
