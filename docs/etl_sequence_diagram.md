# ETL Pipeline Sequence Diagram

This diagram illustrates the high-level control flow of the ETL pipeline, orchestrated by `BatchJob`.

It includes:
- **Extraction**: Fetching records from `GeoNetworkConnector`.
- **Validation**: Validating records using `GeoNetworkValidator`.
- **Transformation**: Processing valid records using `Transformer` (Placeholder).
- **Loading**: Saving processed records using `StoreConnector` (Placeholder).
- **Notification**: Sending alerts and summaries via `NotificationService`.

```mermaid
sequenceDiagram
    participant B as BatchJob
    participant C as GeoNetworkConnector
    participant V as GeoNetworkValidator
    participant T as Transformer
    participant S as StoreConnector
    participant N as NotificationService

    Note over B: Initialization
    B->>C: can_connect()
    activate C
    C-->>B: connection_success
    deactivate C

    Note over B: Extraction Phase
    B->>C: search_records(query)
    activate C
    C-->>B: records (List)
    deactivate C

    Note over B: Processing Loop
    loop For each record
        B->>V: validate(record)
        activate V
        V-->>B: ValidationResult
        deactivate V

        alt Record is Valid
            B->>T: transform(record)
            activate T
            T-->>B: transformed_data
            deactivate T
            
            B->>S: save(transformed_data)
            activate S
            S-->>B: success
            deactivate S
        else Record is Invalid
            B->>N: notify_record_processor_error(details)
            activate N
            N-->>B: void
            deactivate N
        end
    end

    Note over B: Completion
    B->>N: notify_batch_summary(stats)
    activate N
    N-->>B: void
    deactivate N
```
