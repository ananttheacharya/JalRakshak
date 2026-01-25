# AI-Native Virtual Sensing Platform - Requirements

## Overview
Transform JalRakshak from a deterministic, rule-based water monitoring system into an AI-native "Virtual Sensing" platform that can infer water quality at locations without physical sensors using machine learning and upstream data.

## Problem Statement
In developing nations, deploying physical sensors at every water distribution point (especially Level 3 nodes like slums and colonies) is cost-prohibitive. Currently, areas without sensors are "blind" and potentially unsafe, leaving vulnerable populations without water quality monitoring.

## Solution Approach
Implement "Virtual Sensing" using:
- **AI-Inferred Quality**: ML models predict water quality at blind endpoints using upstream sensor data and local hydraulic telemetry
- **Physics-Based Learning**: Models learn fluid dynamics (propagation delay, mixing, contamination spread) 
- **GenAI Universal Alerts**: LLMs convert technical alerts into empathetic, multilingual citizen warnings

## User Stories

### 1. Data Generation & Training
**As a** system administrator  
**I want** to generate realistic training data that simulates contamination propagation through the water network  
**So that** I can train ML models to predict water quality at locations without physical sensors

**Acceptance Criteria:**
- 1.1 System generates synthetic network data with Source (Level 1) and Destination (Level 3) nodes
- 1.2 Contamination events at source propagate to destination with realistic time delays based on flow rate
- 1.3 Training dataset includes: timestamp, source readings, destination hydraulics, true destination quality
- 1.4 Dataset exported as CSV with minimum 1000 samples for training

### 2. Virtual Sensor Model Training
**As a** ML engineer  
**I want** to train models that can predict water quality using only upstream data and local hydraulics  
**So that** blind nodes can have inferred water quality without physical chemical sensors

**Acceptance Criteria:**
- 2.1 Model trains on features: source_turbidity, source_ph, dest_pressure, dest_flow, distance
- 2.2 Model predicts: destination turbidity and pH levels
- 2.3 Model achieves >85% accuracy on test data
- 2.4 Trained model saved as reusable pickle file
- 2.5 Training process outputs performance metrics (MAE, R²)

### 3. Real-Time Inference Service
**As a** monitoring dashboard  
**I want** to query water quality for any node and receive either sensor data or AI predictions  
**So that** all network locations have quality estimates regardless of sensor availability

**Acceptance Criteria:**
- 3.1 Service accepts node ID requests
- 3.2 For nodes with physical sensors: return actual sensor readings
- 3.3 For blind nodes: return AI-predicted quality with confidence scores
- 3.4 Response includes method flag ("SENSOR_READING" vs "AI_INFERRED")
- 3.5 Service handles errors gracefully (missing data, model failures)

### 4. Intelligent Alert Generation
**As a** citizen in a monitored area  
**I want** to receive clear, actionable water quality alerts in my language  
**So that** I can take appropriate safety measures when contamination is detected

**Acceptance Criteria:**
- 4.1 System generates alerts for contamination events (severity levels: LOW, MEDIUM, HIGH)
- 4.2 Alerts include location, contamination type, and specific actions (e.g., "Boil water")
- 4.3 Messages generated in both English and Hindi
- 4.4 Alert length limited to SMS-friendly format (160 characters max)
- 4.5 Tone is urgent but empathetic, avoiding technical jargon

### 5. System Integration
**As a** system operator  
**I want** all AI components to integrate seamlessly with the existing JalRakshak infrastructure  
**So that** the transition to AI-native monitoring is transparent to end users

**Acceptance Criteria:**
- 5.1 Virtual sensing integrates with existing dashboard
- 5.2 AI predictions display alongside sensor data with clear differentiation
- 5.3 Alert system connects to existing notification infrastructure
- 5.4 Performance monitoring tracks AI model accuracy over time
- 5.5 Fallback mechanisms handle AI service failures

## Technical Requirements

### Performance
- Model inference latency: <500ms per request
- Training data generation: Complete within 5 minutes
- Model training: Complete within 10 minutes on standard hardware
- Alert generation: <2 seconds per alert

### Accuracy
- Virtual sensor predictions: >85% accuracy vs ground truth
- Contamination event detection: >90% sensitivity
- False positive rate: <5% for HIGH severity alerts

### Scalability
- Support 100+ network nodes
- Handle 1000+ inference requests per hour
- Training dataset scalable to 10,000+ samples

### Integration
- Compatible with existing MySQL/MariaDB database
- RESTful API for dashboard integration
- Modular design for easy component replacement

## Constraints
- Python 3.9+ environment
- Use scikit-learn/XGBoost for ML models
- AWS Bedrock or mock implementation for GenAI
- Maintain backward compatibility with existing sensor data
- Hackathon-ready code (clear, well-commented, demonstrable)

## Success Metrics
- Reduction in "blind spots": 80% of Level 3 nodes have quality estimates
- Alert response time: Citizens receive warnings within 5 minutes of contamination detection
- Cost reduction: 60% fewer physical sensors needed while maintaining coverage
- User satisfaction: Clear, actionable alerts in preferred language

## Out of Scope
- Hardware sensor modifications
- Network infrastructure changes
- Mobile app development
- Real-time SMS delivery infrastructure
- Production-grade security implementation