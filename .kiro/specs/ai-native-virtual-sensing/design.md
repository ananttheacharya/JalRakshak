# AI-Native Virtual Sensing Platform - Design Document

## Architecture Overview

The AI-native transformation of JalRakshak introduces four core components that work together to provide virtual sensing capabilities:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Data Generator │───▶│   ML Training    │───▶│ Inference Model │
│ (Digital Twin)  │    │    Pipeline      │    │   (Virtual      │
└─────────────────┘    └──────────────────┘    │    Sensor)      │
                                               └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐           │
│   Dashboard     │◀───│ Inference Service│◀──────────┘
│  Integration    │    │   (API Layer)    │
└─────────────────┘    └──────────────────┘
                                │
                       ┌──────────────────┐
                       │  GenAI Alert     │
                       │     System       │
                       └──────────────────┘
```

## Component Design

### 1. Enhanced Data Generator (`sensor_simulator.py`)

**Purpose**: Generate physics-based training data that simulates contamination propagation through water networks.

**Key Design Decisions**:
- **Physics Modeling**: Implement realistic time delays based on distance and flow rate
- **Contamination Events**: Inject spikes at source that propagate downstream
- **Multi-Parameter Simulation**: Generate correlated turbidity and pH changes
- **Temporal Correlation**: Maintain realistic relationships between upstream and downstream readings

**Data Schema**:
```python
{
    'timestamp': datetime,
    'source_turbidity': float,      # NTU units
    'source_ph': float,             # pH scale
    'dest_pressure': float,         # PSI
    'dest_flow': float,             # L/min
    'distance': float,              # meters
    'TRUE_dest_turbidity': float,   # Ground truth label
    'TRUE_dest_ph': float          # Ground truth label
}
```

**Physics Model**:
- Propagation delay: `delay = distance / (flow_rate * pipe_factor)`
- Contamination attenuation: `dest_contamination = source_contamination * exp(-decay_rate * distance)`
- Pressure correlation: Higher pressure indicates better flow, affecting contamination spread

### 2. ML Training Pipeline (`train_inference_model.py`)

**Purpose**: Train regression models to predict water quality at blind nodes using upstream and hydraulic data.

**Model Architecture**:
- **Algorithm**: XGBoost Regressor (handles non-linear relationships well)
- **Multi-target**: Simultaneous prediction of turbidity and pH
- **Feature Engineering**: Time-based features, interaction terms, lag variables

**Feature Set**:
```python
Input Features (X):
- source_turbidity
- source_ph  
- dest_pressure
- dest_flow
- distance
- time_of_day (engineered)
- flow_pressure_ratio (engineered)

Target Variables (Y):
- dest_turbidity
- dest_ph
```

**Training Strategy**:
- Train/validation/test split: 70/15/15
- Cross-validation for hyperparameter tuning
- Feature importance analysis
- Model persistence using pickle

**Performance Metrics**:
- Mean Absolute Error (MAE)
- R-squared (R²)
- Root Mean Square Error (RMSE)
- Feature importance scores

### 3. Inference Service (`inference_service.py`)

**Purpose**: Provide real-time water quality estimates through a unified API that handles both sensor readings and AI predictions.

**Service Architecture**:
```python
class InferenceService:
    def get_water_quality(self, node_id: str) -> WaterQualityResponse
    def _has_physical_sensor(self, node_id: str) -> bool
    def _get_sensor_reading(self, node_id: str) -> dict
    def _predict_quality(self, node_id: str) -> dict
    def _get_hydraulic_data(self, node_id: str) -> dict
```

**Response Format**:
```python
{
    "node_id": "L3_Colony_A",
    "timestamp": "2024-01-25T10:30:00Z",
    "turbidity": 2.3,
    "ph": 7.1,
    "method": "AI_INFERRED",  # or "SENSOR_READING"
    "confidence": 0.92,
    "status": "NORMAL",       # NORMAL, WARNING, CRITICAL
    "metadata": {
        "model_version": "v1.0",
        "features_used": ["source_turbidity", "dest_pressure", ...]
    }
}
```

**Decision Logic**:
1. Check if node has physical sensor (database lookup or configuration)
2. If sensor available: Return direct readings with high confidence
3. If no sensor: Load ML model, gather upstream/hydraulic data, predict quality
4. Apply business rules for status classification (NORMAL/WARNING/CRITICAL)
5. Return structured response with metadata

### 4. GenAI Alert System (`genai_alert_system.py`)

**Purpose**: Generate contextual, multilingual alerts that translate technical water quality data into actionable citizen guidance.

**LLM Integration**:
- **Primary**: AWS Bedrock (Claude/Titan models)
- **Fallback**: Mock implementation for development/demo
- **Prompt Engineering**: Structured prompts for consistent, actionable outputs

**Alert Generation Pipeline**:
```python
def generate_alert(location: str, severity: str, contamination_type: str) -> dict:
    # 1. Construct context-aware prompt
    # 2. Call LLM with structured prompt
    # 3. Parse and validate response
    # 4. Return bilingual alert
```

**Prompt Template**:
```
You are JalRakshak, a water safety AI assistant for Indian communities.

Context:
- Location: {location}
- Severity: {severity} (LOW/MEDIUM/HIGH)
- Contamination: {contamination_type}

Generate an urgent but empathetic SMS alert (max 160 chars) that:
1. States the problem clearly
2. Gives specific action (boil water, avoid drinking, etc.)
3. Maintains calm but urgent tone

Provide response in JSON format with English and Hindi versions.
```

**Output Format**:
```python
{
    "english": "HIGH contamination detected in Colony A. BOIL water for 5 mins before drinking. Avoid direct consumption. -JalRakshak",
    "hindi": "कॉलोनी A में उच्च संदूषण। पीने से पहले 5 मिनट उबालें। सीधे सेवन से बचें। -जलरक्षक",
    "severity": "HIGH",
    "actions": ["boil_water", "avoid_direct_consumption"],
    "timestamp": "2024-01-25T10:30:00Z"
}
```

## Data Flow Architecture

### Training Phase
1. **Data Generation**: `sensor_simulator.py` creates `training_data.csv`
2. **Model Training**: `train_inference_model.py` processes CSV, trains model, saves `virtual_sensor_model.pkl`
3. **Validation**: Performance metrics validate model readiness

### Inference Phase
1. **Request**: Dashboard/API calls `inference_service.py` with node_id
2. **Decision**: Service determines if node has physical sensor
3. **Data Gathering**: Collect upstream sensor data + local hydraulic data
4. **Prediction**: Load model, predict water quality if needed
5. **Response**: Return structured quality assessment
6. **Alerting**: If contamination detected, trigger `genai_alert_system.py`

## Integration Points

### Database Schema Extensions
```sql
-- Node configuration table
CREATE TABLE node_config (
    node_id VARCHAR(50) PRIMARY KEY,
    node_type ENUM('L1_SOURCE', 'L2_INTERMEDIATE', 'L3_ENDPOINT'),
    has_physical_sensor BOOLEAN,
    upstream_node_id VARCHAR(50),
    distance_from_source FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI predictions log
CREATE TABLE ai_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    node_id VARCHAR(50),
    predicted_turbidity FLOAT,
    predicted_ph FLOAT,
    confidence_score FLOAT,
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints
```python
# New endpoints for AI-native functionality
GET /api/v2/nodes/{node_id}/quality     # Unified quality endpoint
GET /api/v2/nodes/{node_id}/prediction  # Force AI prediction
POST /api/v2/alerts/generate            # Generate custom alert
GET /api/v2/model/status                # Model health check
```

## Correctness Properties

### Property 1: Prediction Accuracy Bounds
**Requirement**: Virtual sensor predictions must maintain accuracy within acceptable bounds
**Property**: For any prediction P and ground truth G: `|P - G| / G <= 0.15` (15% tolerance)
**Test Strategy**: Property-based testing with generated scenarios

### Property 2: Temporal Consistency  
**Requirement**: Predictions should be temporally consistent (no sudden jumps)
**Property**: For consecutive predictions P1, P2: `|P2 - P1| <= max_change_threshold`
**Test Strategy**: Generate time series and verify smoothness

### Property 3: Alert Completeness
**Requirement**: All contamination events above threshold must generate alerts
**Property**: If contamination_level > CRITICAL_THRESHOLD, then alert_generated = True
**Test Strategy**: Inject contamination events and verify alert generation

### Property 4: Bilingual Alert Consistency
**Requirement**: English and Hindi alerts must convey the same information
**Property**: Both language versions must contain equivalent severity and action terms
**Test Strategy**: Semantic similarity testing between translations

## Performance Considerations

### Model Optimization
- **Feature Selection**: Use correlation analysis to remove redundant features
- **Model Compression**: Quantize model weights for faster inference
- **Caching**: Cache predictions for frequently queried nodes
- **Batch Processing**: Support batch inference for multiple nodes

### Scalability Design
- **Horizontal Scaling**: Stateless service design for load balancing
- **Model Versioning**: Support A/B testing of model versions
- **Monitoring**: Track prediction accuracy, latency, and error rates
- **Graceful Degradation**: Fallback to rule-based estimates if ML fails

## Security & Privacy

### Data Protection
- **Anonymization**: Remove personally identifiable location data from training sets
- **Encryption**: Encrypt model files and sensitive configuration
- **Access Control**: Role-based access to prediction APIs
- **Audit Logging**: Log all predictions and alert generations

### Model Security
- **Input Validation**: Sanitize all input features before prediction
- **Output Bounds**: Clamp predictions to physically reasonable ranges
- **Model Integrity**: Verify model checksums before loading
- **Adversarial Robustness**: Test against input perturbations

## Testing Strategy

### Unit Testing
- Individual component testing for each module
- Mock external dependencies (database, LLM APIs)
- Edge case handling (missing data, invalid inputs)

### Integration Testing  
- End-to-end workflow testing
- Database integration validation
- API contract testing

### Property-Based Testing
- Generate random but valid input scenarios
- Verify correctness properties hold across input space
- Test model robustness with edge cases

### Performance Testing
- Load testing for concurrent inference requests
- Memory usage profiling during model training
- Latency benchmarking for real-time requirements

## Deployment Strategy

### Development Environment
- Local SQLite database for rapid iteration
- Mock LLM responses for offline development
- Containerized services for consistent environments

### Production Considerations
- Model monitoring and drift detection
- Automated retraining pipelines
- Blue-green deployment for model updates
- Comprehensive logging and alerting

This design provides a robust foundation for transforming JalRakshak into an AI-native platform while maintaining reliability and user trust.