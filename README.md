# EdgeSphere AI - Enterprise IoT Device Management Platform

[![CI/CD Pipeline](https://github.com/NICHOLASKARANI/edge-sphere-ai/actions/workflows/deploy.yml/badge.svg)](https://github.com/NICHOLASKARANI/edge-sphere-ai/actions/workflows/deploy.yml)
[![Code Coverage](https://codecov.io/gh/NICHOLASKARANI/edge-sphere-ai/branch/main/graph/badge.svg)](https://codecov.io/gh/NICHOLASKARANI/edge-sphere-ai)
[![Docker Pulls](https://img.shields.io/docker/pulls/edgesphere/backend)](https://hub.docker.com/r/edgesphere/backend)

## 🚀 Overview

EdgeSphere AI is an enterprise-grade IoT device management platform that competes with AWS IoT Core and Azure IoT Central. It provides comprehensive device fleet management, AI-driven anomaly detection, predictive maintenance, and real-time analytics for IoT deployments.

## ✨ Key Features

- **Device Fleet Management**: Onboarding, provisioning, monitoring, and remote configuration
- **AI Anomaly Detection**: Real-time detection of device anomalies using LSTM autoencoders
- **Predictive Maintenance**: Failure prediction and remaining useful life estimation
- **OTA Updates**: Secure over-the-air firmware updates for all device types
- **Multi-Cloud Support**: AWS IoT Core, Azure IoT Hub, or self-hosted MQTT
- **Real-time Dashboard**: React/TypeScript dashboard with live telemetry
- **Enterprise Security**: TLS, certificate authentication, secure firmware updates
- **Edge Device Support**: ESP32, STM32, Raspberry Pi, Arduino

## 🏗 Architecture
┌─────────────────────────────────────────────────────────────┐
│ EdgeSphere AI Platform │
├─────────────────────────────────────────────────────────────┤
│ Dashboard (React/TS) │ API Gateway (FastAPI) │ AI/ML │
├─────────────────────────────────────────────────────────────┤
│ MQTT Broker │ Kafka Streams │ PostgreSQL │ Redis │ MinIO │
├─────────────────────────────────────────────────────────────┤
│ Edge Devices (ESP32, STM32, RPi, Arduino) │
└─────────────────────────────────────────────────────────────┘

## 📦 Installation

### Prerequisites
- Docker & Docker Compose
- Kubernetes cluster (for production)
- Python 3.11+
- Node.js 18+
- ESP32/STM32 toolchains (for firmware development)

### Quick Start (Development)

1. **Clone the repository**
```bash
git clone https://github.com/NICHOLASKARANI/edge-sphere-ai.git
cd edge-sphere-ai