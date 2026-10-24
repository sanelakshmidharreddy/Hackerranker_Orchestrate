================================================================================
GHOST DATA STILL EXISTS — DATASET PROFILING REPORT
================================================================================

### 1. CSV Row Counts in dataset/
  - deletion_requests.csv: 518 data rows | Header: ['case_id', 'email', 'requested_at', 'reported_status', 'reported_at', 'audit_at', 'request_text']
  - deletion_rules.csv: 15 data rows | Header: ['rule_id', 'data_category', 'condition', 'required_action']
  - evidence_files.csv: 94 data rows | Header: ['file_id', 'file_path', 'origin', 'captured_at']
  - output.csv: 0 data rows | Header: ['case_id', 'deletion_status', 'steps_json']
  - sample_deletion_requests.csv: 32 data rows | Header: ['case_id', 'email', 'requested_at', 'reported_status', 'reported_at', 'audit_at', 'request_text']
  - sample_output.csv: 32 data rows | Header: ['case_id', 'deletion_status', 'steps_json']
  - system_activity.csv: 4011 data rows | Header: ['activity_id', 'event_time', 'event_type', 'source_system', 'target_system', 'resource_id', 'reported_result', 'details']
  - user_audit_log.csv: 306 data rows | Header: ['audit_id', 'user_id', 'event_time', 'field_name', 'old_value', 'new_value']
  - user_identities.csv: 850 data rows | Header: ['user_id', 'name', 'email', 'phone', 'email_hash', 'updated_at']

### 2. Value Counts from CSVs

* deletion_requests.csv reported_status (total 518):
    COMPLETE: 254
    PARTIALLY_COMPLETE: 152
    NOT_STARTED: 112

* sample_deletion_requests.csv reported_status (total 32):
    COMPLETE: 17
    NOT_STARTED: 10
    PARTIALLY_COMPLETE: 5

* sample_output.csv deletion_status (total 32):
    INCOMPLETE: 22
    COMPLETE: 10

* system_activity.csv event_type (total 4011):
    DELETE_RECORD               : 890
    UPDATE_RECORD               : 672
    SYNC_RECORD                 : 447
    INDEX_RECORD                : 400
    SEND_EMAIL                  : 368
    REFRESH_CACHE               : 284
    RETAIN_RECORD               : 206
    ANONYMIZE_RECORD            : 204
    REDACT_RECORD               : 173
    CREATE_EXPORT               : 155
    CHECK_DATA_FLOW             : 89
    DISABLE_DATA_FLOW           : 36
    BLOCK_RESTORE               : 36
    CHECK_RESTORE_ACCESS        : 28
    LINK_RESOURCE_IDENTITY      : 12
    CLASSIFY_REQUEST            : 10
    RESTORE_BACKUP              : 1

* system_activity.csv reported_result (total 4011):
    SUCCESS        : 2914
    FAILED         : 721
    PARTIAL        : 376

* system_activity.csv target_system (top 15 of 19):
    account_service               : 980
    search_service                : 954
    analytics_platform            : 566
    email_delivery_service        : 368
    cache_service                 : 284
    archive_service               : 196
    support_platform              : 193
    object_store                  : 155
    integration_service           : 126
    backup_service                : 65
    account_replication_cluster   : 55
    export_service                : 34
    identity_service              : 11
    legal_service                 : 10
    privacy_case_management       : 10

* system_activity.csv source_system (top 15 of 11):
    deletion_worker               : 1466
    account_service               : 1100
    profile_service               : 440
    notification_service          : 368
    support_platform              : 232
    security_service              : 196
    export_service                : 155
    integration_service           : 31
    data_catalog                  : 12
    privacy_intake                : 10
    backup_service                : 1

* system_activity.csv resource_id prefixes:
    account_            : 1046
    search_             : 690
    analytics_          : 566
    support_            : 425
    email_              : 368
    cache_              : 284
    audit_              : 197
    export_             : 189
    data_               : 157
    backup_             : 66
    tombstone_          : 11
    legal_              : 10
    object_             : 1
    marketing_          : 1

* user_audit_log.csv field_name (total 306):
    email          : 107
    email_hash     : 107
    phone          : 92

### 3. Distinct request_text Values in deletion_requests.csv (375 distinct)
Count  | First 80 characters                                                             
------------------------------------------------------------------------------------------
14     | Solicito a exclusão permanente da conta associada a este e-mail. Verifiquem os i
12     | 이 이메일 주소에 연결된 계정의 영구 삭제를 요청합니다. 개인정보 처리 절차에 따라 현재 및 이전 식별자를 검토해 주세요. 검토가 완료되면 결과
12     | Solicito la eliminación permanente de la cuenta asociada a este correo. Revisen
12     | このメールアドレスに関連するアカウントの完全な削除を依頼します。 プライバシー手続きに従い、現在および過去の識別情報を確認してください。 確認が完了したら結果を
12     | Je demande la suppression définitive du compte associé à cette adresse e-mail. V
3      | Please erase the account linked to this email address. Please handle any copies
3      | Please treat this message as a request for permanent account deletion. Please re
3      | Please permanently delete the account associated with this email address. Please
3      | Please treat this message as a request for permanent account deletion. Please ap
3      | I would like to submit a request to delete this account and its personal data. P
3      | Please treat this message as a request for permanent account deletion. Please ap
3      | Please erase the account linked to this email address. Please check the records
3      | Please erase the account linked to this email address. Please review the account
3      | I am requesting deletion of the account registered to this email address. Please
3      | I no longer use this account and would like it permanently deleted. Please revie
3      | Please treat this message as a request for permanent account deletion. Please re
2      | Please close my account and process the associated personal-data deletion. Pleas
2      | Please erase the account linked to this email address. Please check the records
2      | I am requesting deletion of the account registered to this email address. Please
2      | I no longer use this account and would like it permanently deleted. Please proce
2      | I am asking you to remove my account and the personal information linked to it.
2      | Please treat this message as a request for permanent account deletion. Please in
2      | I would like the account associated with this address to be erased. Please revie
2      | I would like to submit a request to delete this account and its personal data. P
2      | Please treat this message as a request for permanent account deletion. Please ch
2      | Please permanently delete the account associated with this email address. Please
2      | I am asking you to remove my account and the personal information linked to it.
2      | I no longer use this account and would like it permanently deleted. Please follo
2      | I am requesting deletion of the account registered to this email address. Please
2      | Please treat this message as a request for permanent account deletion. Please ap
2      | Please close my account and process the associated personal-data deletion. Pleas
2      | I am requesting deletion of the account registered to this email address. Please
2      | Please process a permanent account-deletion request for this email address. Plea
2      | I want to close this account and have its associated personal data deleted. Plea
2      | Please treat this message as a request for permanent account deletion. Please ap
2      | I would like to submit a request to delete this account and its personal data. P
2      | I would like to submit a request to delete this account and its personal data. P
2      | I am requesting deletion of the account registered to this email address. Please
2      | Please treat this message as a request for permanent account deletion. Please re
2      | I would like to submit a request to delete this account and its personal data. P
2      | Please begin the deletion process for the account using this email address. Plea
2      | I am asking you to remove my account and the personal information linked to it.
2      | I am requesting deletion of the account registered to this email address. Please
2      | Please begin the deletion process for the account using this email address. Plea
2      | Please process a permanent account-deletion request for this email address. Plea
2      | I would like the account associated with this address to be erased. Please compl
2      | I am asking you to remove my account and the personal information linked to it.
2      | I am asking you to remove my account and the personal information linked to it.
2      | Please close my account and process the associated personal-data deletion. Pleas
2      | Please erase the account linked to this email address. Please include records as
2      | Please erase the account linked to this email address. Please process this under
2      | Please begin the deletion process for the account using this email address. Plea
2      | I am asking you to remove my account and the personal information linked to it.
2      | Please permanently delete the account associated with this email address. Please
2      | Please process a permanent account-deletion request for this email address. Plea
2      | I am asking you to remove my account and the personal information linked to it.
2      | Please close my account and process the associated personal-data deletion. Pleas
2      | Please begin the deletion process for the account using this email address. Plea
2      | I no longer use this account and would like it permanently deleted. Please follo
2      | I would like the account associated with this address to be erased. Please ensur
2      | Please close my account and process the associated personal-data deletion. Pleas
2      | Please erase the account linked to this email address. Please complete the norma
2      | Please process a permanent account-deletion request for this email address. Plea
2      | Please permanently delete the account associated with this email address. Please
2      | I am asking you to remove my account and the personal information linked to it.
2      | I am asking you to remove my account and the personal information linked to it.
2      | Please begin the deletion process for the account using this email address. Plea
2      | I would like the account associated with this address to be erased. Please apply
2      | I would like to submit a request to delete this account and its personal data. P
2      | Please begin the deletion process for the account using this email address. Plea
2      | I no longer use this account and would like it permanently deleted. Please inclu
2      | I no longer use this account and would like it permanently deleted. Please revie
2      | Please treat this message as a request for permanent account deletion. Please ha
2      | Please begin the deletion process for the account using this email address. Plea
2      | Please permanently delete the account associated with this email address. Please
2      | I no longer use this account and would like it permanently deleted. Please apply
2      | Please treat this message as a request for permanent account deletion. Please fo
2      | I am requesting deletion of the account registered to this email address. Please
2      | Please treat this message as a request for permanent account deletion. Please re
2      | Please permanently delete the account associated with this email address. Please
1      | I would like the account associated with this address to be erased. Please handl
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | I want to close this account and have its associated personal data deleted. Plea
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I would like to submit a request to delete this account and its personal data. P
1      | I am asking you to remove my account and the personal information linked to it.
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I am requesting deletion of the account registered to this email address. Please
1      | I want to close this account and have its associated personal data deleted. Plea
1      | I no longer use this account and would like it permanently deleted. Please apply
1      | Please treat this message as a request for permanent account deletion. Please ch
1      | I am requesting deletion of the account registered to this email address. Please
1      | Please erase the account linked to this email address. Please apply the correct
1      | I am asking you to remove my account and the personal information linked to it.
1      | Please erase the account linked to this email address. Please handle any copies
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please begin the deletion process for the account using this email address. Plea
1      | Please treat this message as a request for permanent account deletion. Please ap
1      | I no longer use this account and would like it permanently deleted. Please ensur
1      | I am requesting deletion of the account registered to this email address. Please
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I am asking you to remove my account and the personal information linked to it.
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please begin the deletion process for the account using this email address. Plea
1      | Please erase the account linked to this email address. Please review the account
1      | I want to close this account and have its associated personal data deleted. Plea
1      | I would like the account associated with this address to be erased. Please handl
1      | Please permanently delete the account associated with this email address. Please
1      | I am requesting deletion of the account registered to this email address. Please
1      | I would like to submit a request to delete this account and its personal data. P
1      | I would like to submit a request to delete this account and its personal data. P
1      | I want to close this account and have its associated personal data deleted. Plea
1      | I no longer use this account and would like it permanently deleted. Please revie
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please treat this message as a request for permanent account deletion. Please in
1      | Please permanently delete the account associated with this email address. Please
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | Please erase the account linked to this email address. Please follow the applica
1      | I am requesting deletion of the account registered to this email address. Please
1      | I want to close this account and have its associated personal data deleted. Plea
1      | Please treat this message as a request for permanent account deletion. Please in
1      | I no longer use this account and would like it permanently deleted. Please inclu
1      | Please permanently delete the account associated with this email address. Please
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please treat this message as a request for permanent account deletion. Please in
1      | I am requesting deletion of the account registered to this email address. Please
1      | I am asking you to remove my account and the personal information linked to it.
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please process a permanent account-deletion request for this email address. Plea
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | Please erase the account linked to this email address. Please review the account
1      | Please treat this message as a request for permanent account deletion. Please in
1      | Please permanently delete the account associated with this email address. Please
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I am asking you to remove my account and the personal information linked to it.
1      | I would like the account associated with this address to be erased. Please inclu
1      | I want to close this account and have its associated personal data deleted. Plea
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I no longer use this account and would like it permanently deleted. Please revie
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I am asking you to remove my account and the personal information linked to it.
1      | Please permanently delete the account associated with this email address. Please
1      | Please permanently delete the account associated with this email address. Please
1      | I no longer use this account and would like it permanently deleted. Please compl
1      | Please treat this message as a request for permanent account deletion. Please in
1      | I would like the account associated with this address to be erased. Please apply
1      | Please begin the deletion process for the account using this email address. Plea
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | I no longer use this account and would like it permanently deleted. Please inclu
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | I no longer use this account and would like it permanently deleted. Please compl
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | Please permanently delete the account associated with this email address. Please
1      | Please erase the account linked to this email address. Please include records as
1      | Please begin the deletion process for the account using this email address. Plea
1      | Please erase the account linked to this email address. Please ensure the request
1      | Please process a permanent account-deletion request for this email address. Plea
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I no longer use this account and would like it permanently deleted. Please follo
1      | I am requesting deletion of the account registered to this email address. Please
1      | I want to close this account and have its associated personal data deleted. Plea
1      | Please treat this message as a request for permanent account deletion. Please ap
1      | I am requesting deletion of the account registered to this email address. Please
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | I am requesting deletion of the account registered to this email address. Please
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please treat this message as a request for permanent account deletion. Please re
1      | Please treat this message as a request for permanent account deletion. Please en
1      | Please process a permanent account-deletion request for this email address. Plea
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I would like the account associated with this address to be erased. Please inclu
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | Please treat this message as a request for permanent account deletion. Please ch
1      | I am requesting deletion of the account registered to this email address. Please
1      | I want to close this account and have its associated personal data deleted. Plea
1      | Please erase the account linked to this email address. Please process this under
1      | I would like the account associated with this address to be erased. Please handl
1      | I am asking you to remove my account and the personal information linked to it.
1      | Please erase the account linked to this email address. Please include informatio
1      | Please permanently delete the account associated with this email address. Please
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please permanently delete the account associated with this email address. Please
1      | Please erase the account linked to this email address. Please follow the applica
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | I would like to submit a request to delete this account and its personal data. P
1      | I am requesting deletion of the account registered to this email address. Please
1      | I am requesting deletion of the account registered to this email address. Please
1      | Please permanently delete the account associated with this email address. Please
1      | I am requesting deletion of the account registered to this email address. Please
1      | Please permanently delete the account associated with this email address. Please
1      | I would like to submit a request to delete this account and its personal data. P
1      | I would like to submit a request to delete this account and its personal data. P
1      | I would like the account associated with this address to be erased. Please ensur
1      | Please treat this message as a request for permanent account deletion. Please en
1      | Please process a permanent account-deletion request for this email address. Plea
1      | Please erase the account linked to this email address. Please review the account
1      | Please treat this message as a request for permanent account deletion. Please re
1      | I am asking you to remove my account and the personal information linked to it.
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | Please erase the account linked to this email address. Please apply the correct
1      | I am asking you to remove my account and the personal information linked to it.
1      | Please erase the account linked to this email address. Please review the account
1      | Please permanently delete the account associated with this email address. Please
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | I am asking you to remove my account and the personal information linked to it.
1      | I no longer use this account and would like it permanently deleted. Please follo
1      | Please permanently delete the account associated with this email address. Please
1      | I would like the account associated with this address to be erased. Please inclu
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | I no longer use this account and would like it permanently deleted. Please revie
1      | I would like the account associated with this address to be erased. Please apply
1      | I no longer use this account and would like it permanently deleted. Please ensur
1      | I no longer use this account and would like it permanently deleted. Please check
1      | Please begin the deletion process for the account using this email address. Plea
1      | Please erase the account linked to this email address. Please apply the request
1      | I no longer use this account and would like it permanently deleted. Please proce
1      | Please erase the account linked to this email address. Please ensure the request
1      | Please permanently delete the account associated with this email address. Please
1      | I would like the account associated with this address to be erased. Please inclu
1      | I no longer use this account and would like it permanently deleted. Please proce
1      | I would like the account associated with this address to be erased. Please revie
1      | I am asking you to remove my account and the personal information linked to it.
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | I would like the account associated with this address to be erased. Please revie
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | Please begin the deletion process for the account using this email address. Plea
1      | Please erase the account linked to this email address. Please apply the correct
1      | I am asking you to remove my account and the personal information linked to it.
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please begin the deletion process for the account using this email address. Plea
1      | I am asking you to remove my account and the personal information linked to it.
1      | I want to close this account and have its associated personal data deleted. Plea
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I am requesting deletion of the account registered to this email address. Please
1      | I want to close this account and have its associated personal data deleted. Plea
1      | I no longer use this account and would like it permanently deleted. Please check
1      | Please treat this message as a request for permanent account deletion. Please ha
1      | I would like the account associated with this address to be erased. Please inclu
1      | Please erase the account linked to this email address. Please process this under
1      | I am requesting deletion of the account registered to this email address. Please
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I am asking you to remove my account and the personal information linked to it.
1      | I am requesting deletion of the account registered to this email address. Please
1      | I no longer use this account and would like it permanently deleted. Please ensur
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please treat this message as a request for permanent account deletion. Please en
1      | I would like to submit a request to delete this account and its personal data. P
1      | I would like the account associated with this address to be erased. Please compl
1      | I no longer use this account and would like it permanently deleted. Please proce
1      | I am requesting deletion of the account registered to this email address. Please
1      | I want to close this account and have its associated personal data deleted. Plea
1      | Please treat this message as a request for permanent account deletion. Please ch
1      | Please begin the deletion process for the account using this email address. Plea
1      | I no longer use this account and would like it permanently deleted. Please revie
1      | I no longer use this account and would like it permanently deleted. Please check
1      | I would like to submit a request to delete this account and its personal data. P
1      | I would like the account associated with this address to be erased. Please apply
1      | I am requesting deletion of the account registered to this email address. Please
1      | Please erase the account linked to this email address. Please apply the request
1      | Please erase the account linked to this email address. Please apply the request
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | I want to close this account and have its associated personal data deleted. Plea
1      | Please treat this message as a request for permanent account deletion. Please ha
1      | Please erase the account linked to this email address. Please review the account
1      | Please permanently delete the account associated with this email address. Please
1      | I am asking you to remove my account and the personal information linked to it.
1      | Please permanently delete the account associated with this email address. Please
1      | I am asking you to remove my account and the personal information linked to it.
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please permanently delete the account associated with this email address. Please
1      | I want to close this account and have its associated personal data deleted. Plea
1      | Please treat this message as a request for permanent account deletion. Please pr
1      | I no longer use this account and would like it permanently deleted. Please ensur
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I want to close this account and have its associated personal data deleted. Plea
1      | I am requesting deletion of the account registered to this email address. Please
1      | I am requesting deletion of the account registered to this email address. Please
1      | I would like the account associated with this address to be erased. Please follo
1      | Please treat this message as a request for permanent account deletion. Please in
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | I am requesting deletion of the account registered to this email address. Please
1      | I am asking you to remove my account and the personal information linked to it.
1      | I would like to submit a request to delete this account and its personal data. P
1      | I am requesting deletion of the account registered to this email address. Please
1      | Please begin the deletion process for the account using this email address. Plea
1      | Please permanently delete the account associated with this email address. Please
1      | I would like the account associated with this address to be erased. Please inclu
1      | I would like to submit a request to delete this account and its personal data. P
1      | I want to close this account and have its associated personal data deleted. Plea
1      | I would like to submit a request to delete this account and its personal data. P
1      | I want to close this account and have its associated personal data deleted. Plea
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please erase the account linked to this email address. Please follow the applica
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please treat this message as a request for permanent account deletion. Please ap
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please treat this message as a request for permanent account deletion. Please en
1      | I am requesting deletion of the account registered to this email address. Please
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | Please process a permanent account-deletion request for this email address. Plea
1      | Please begin the deletion process for the account using this email address. Plea
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please begin the deletion process for the account using this email address. Plea
1      | I want to close this account and have its associated personal data deleted. Plea
1      | I am asking you to remove my account and the personal information linked to it.
1      | Please treat this message as a request for permanent account deletion. Please co
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please close my account and process the associated personal-data deletion. Pleas
1      | I am requesting deletion of the account registered to this email address. Please
1      | Please permanently delete the account associated with this email address. Please
1      | I am requesting deletion of the account registered to this email address. Please
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please permanently delete the account associated with this email address. Please
1      | I am requesting deletion of the account registered to this email address. Please
1      | I want to close this account and have its associated personal data deleted. Plea
1      | Please erase the account linked to this email address. Please review any identif
1      | Please permanently delete the account associated with this email address. Please
1      | Please treat this message as a request for permanent account deletion. Please ch
1      | Please erase the account linked to this email address. Please process this under
1      | I want to close this account and have its associated personal data deleted. Plea
1      | I would like to submit a request to delete this account and its personal data. P
1      | I would like the account associated with this address to be erased. Please apply
1      | I would like the account associated with this address to be erased. Please revie
1      | I am asking you to remove my account and the personal information linked to it.
1      | Please begin the deletion process for the account using this email address. Plea
1      | I want to close this account and have its associated personal data deleted. Plea
1      | I am requesting deletion of the account registered to this email address. Please
1      | Please begin the deletion process for the account using this email address. Plea
1      | Please treat this message as a request for permanent account deletion. Please re
1      | I am requesting deletion of the account registered to this email address. Please
1      | Please erase the account linked to this email address. Please apply the correct
1      | I am requesting deletion of the account registered to this email address. Please
1      | Please erase the account linked to this email address. Please process this under
1      | I am requesting deletion of the account registered to this email address. Please
1      | I would like the account associated with this address to be erased. Please inclu
1      | I am asking you to remove my account and the personal information linked to it.
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I would like to submit a request to delete this account and its personal data. P
1      | I would like to submit a request to delete this account and its personal data. P
1      | I would like to submit a request to delete this account and its personal data. P
1      | I am asking you to remove my account and the personal information linked to it.
1      | I want to close this account and have its associated personal data deleted. Plea
1      | I no longer use this account and would like it permanently deleted. Please revie
1      | Please begin the deletion process for the account using this email address. Plea
1      | Please erase the account linked to this email address. Please apply the request
1      | I am requesting deletion of the account registered to this email address. Please
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please process a permanent account-deletion request for this email address. Plea
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please erase the account linked to this email address. Please include informatio
1      | Please process a permanent account-deletion request for this email address. Plea
1      | Please erase the account linked to this email address. Please handle any copies
1      | I would like to submit a request to delete this account and its personal data. P
1      | Please permanently delete the account associated with this email address. Please
1      | I would like the account associated with this address to be erased. Please check
1      | The mobile number on my profile is out of date. Please replace it with the new o
1      | Please stop the promotional emails. I still need the account and my order histor
1      | I'd like to download my account information in a portable format. Please keep th
1      | I can't access my profile and need help resetting the login. Do not close the ac
1      | My surname is misspelled on the account. Can you correct it without removing any
1      | Please remove me from marketing lists only. I still want receipts and service me
1      | Can you tell me what personal information you hold about me? This is an informat
1      | I need a copy of last year's invoices for my records. Please leave my profile an
1      | Please change the email address used for this account. I want to continue using
1      | Could you send me a copy of the information held on my account? I still use it,
1      | Please process a permanent account-deletion request for this email address. Plea
1      | Please begin the deletion process for the account using this email address. Plea
1      | Please permanently delete the account associated with this email address. Please
1      | Please permanently delete the account associated with this email address. Please

### 4. Email Hash Verification (user_identities.csv)
  Total users checked: 850
  Email hash mismatches: 0

### 5. Evidence Files Manifest (evidence_files.csv)
  Total evidence files: 94
  Counts by folder:
    evidence       : 94
  Counts by origin:
    central_observability_export  : 12
    records_assurance_snapshot_bundle: 12
    service_resource_export       : 11
    customer_data_inventory_capture: 11
    service_readback_logs         : 11
    customer_data_read_replica_capture: 5
    support_platform              : 3
    customer_data_regional_replicas_capture: 3
    analytics_platform            : 2
    export_service                : 2
    security_service              : 2
    customer_data_reporting_replica_capture: 2
    customer_account_service      : 1
    account_admin_portal          : 1
    search_index_service          : 1
    search_index_admin            : 1
    integration_management_service: 1
    integration_admin             : 1
    account_history_service       : 1
    legal_retention_service       : 1
    backup_service                : 1
    customer_export_service       : 1
    downstream_delivery_service   : 1
    identity_service              : 1
    object_storage                : 1
    security_audit_service        : 1
    customer_data_failover_replica_capture: 1
    customer_account_failover_replica_capture: 1
    customer_search_primary_capture: 1
    marketing_platform            : 1
  Min captured_at: 2026-01-29T11:44:59Z
  Max captured_at: 2026-10-01T12:00:00Z

### 6. SQL Files Analysis (.sql under evidence/databases/)
  Found 24 SQL files.
  - customer_accounts_failover_replica_20260902.sql: customer_profiles_failover_replica(4), customer_profiles_primary(3)
  - customer_data_failover_replica_20260920.sql: customer_data_failover_replica(16), customer_data_primary(16)
  - customer_data_inventory_20260213.sql: snapshot_scope(7), customer_profiles(2), customer_search_documents(4), customer_analytics_profiles(3), support_records(2), customer_exports(0), connector_subscriptions(1), backup_restore_entries(1), security_audit_records(4)
  - customer_data_inventory_20260310.sql: snapshot_scope(8), customer_profiles(0), customer_search_documents(7), customer_analytics_profiles(5), support_records(3), customer_exports(1), connector_subscriptions(4), backup_restore_entries(1), security_audit_records(2)
  - customer_data_inventory_20260404.sql: snapshot_scope(8), customer_profiles(0), customer_search_documents(5), customer_analytics_profiles(4), support_records(2), customer_exports(1), connector_subscriptions(2), backup_restore_entries(1), security_audit_records(3)
  - customer_data_inventory_20260504.sql: snapshot_scope(7), customer_profiles(1), customer_search_documents(6), customer_analytics_profiles(3), support_records(3), customer_exports(0), connector_subscriptions(4), backup_restore_entries(1), security_audit_records(3)
  - customer_data_inventory_20260524.sql: snapshot_scope(8), customer_profiles(0), customer_search_documents(5), customer_analytics_profiles(6), support_records(3), customer_exports(1), connector_subscriptions(4), backup_restore_entries(1), security_audit_records(4)
  - customer_data_inventory_20260618.sql: snapshot_scope(7), customer_profiles(2), customer_search_documents(6), customer_analytics_profiles(4), support_records(3), customer_exports(1), connector_subscriptions(1), backup_restore_entries(0), security_audit_records(2)
  - customer_data_inventory_20260703.sql: snapshot_scope(8), customer_profiles(0), customer_search_documents(5), customer_analytics_profiles(5), support_records(5), customer_exports(1), connector_subscriptions(2), backup_restore_entries(1), security_audit_records(5)
  - customer_data_inventory_20260723.sql: snapshot_scope(8), customer_profiles(1), customer_search_documents(7), customer_analytics_profiles(5), support_records(5), customer_exports(1), connector_subscriptions(4), backup_restore_entries(1), security_audit_records(2)
  - customer_data_inventory_20260817.sql: snapshot_scope(8), customer_profiles(1), customer_search_documents(5), customer_analytics_profiles(4), support_records(4), customer_exports(1), connector_subscriptions(1), backup_restore_entries(1), security_audit_records(2)
  - customer_data_inventory_20260905.sql: snapshot_scope(1), customer_profiles(0), customer_search_documents(0), customer_analytics_profiles(0), support_records(0), customer_exports(0), connector_subscriptions(0), backup_restore_entries(0), security_audit_records(0)
  - customer_data_inventory_20260916.sql: snapshot_scope(8), customer_profiles(1), customer_search_documents(3), customer_analytics_profiles(2), support_records(3), customer_exports(1), connector_subscriptions(2), backup_restore_entries(2), security_audit_records(3)
  - customer_data_read_replica_20260613.sql: customer_data_primary(24), customer_data_read_replica(26)
  - customer_data_read_replica_20260708.sql: customer_data_primary(31), customer_data_read_replica(32)
  - customer_data_read_replica_20260802.sql: customer_data_primary(24), customer_data_read_replica(25)
  - customer_data_read_replica_20260827.sql: customer_data_primary(29), customer_data_read_replica(30)
  - customer_data_read_replica_20260921.sql: customer_data_primary(30), customer_data_read_replica(31)
  - customer_data_regional_replicas_20260330.sql: customer_data_primary(28), customer_data_replica_ap_south(29), customer_data_replica_eu_west(28)
  - customer_data_regional_replicas_20260424.sql: customer_data_primary(29), customer_data_replica_ap_south(29), customer_data_replica_eu_west(31)
  - customer_data_regional_replicas_20260519.sql: customer_data_primary(28), customer_data_replica_ap_south(29), customer_data_replica_eu_west(28)
  - customer_data_reporting_replica_20260208.sql: customer_data_primary(24), customer_data_reporting_replica(25)
  - customer_data_reporting_replica_20260305.sql: customer_data_primary(25), customer_data_reporting_replica(26)
  - customer_search_primary_20260910.sql: search_documents_primary(3)

  Aggregated SQL table occurrences across all files:
    customer_data_primary         : seen in 11 files
    snapshot_scope                : seen in 11 files
    customer_profiles             : seen in 11 files
    customer_search_documents     : seen in 11 files
    customer_analytics_profiles   : seen in 11 files
    support_records               : seen in 11 files
    customer_exports              : seen in 11 files
    connector_subscriptions       : seen in 11 files
    backup_restore_entries        : seen in 11 files
    security_audit_records        : seen in 11 files
    customer_data_read_replica    : seen in 5 files
    customer_data_replica_ap_south: seen in 3 files
    customer_data_replica_eu_west : seen in 3 files
    customer_data_reporting_replica: seen in 2 files
    customer_profiles_failover_replica: seen in 1 files
    customer_profiles_primary     : seen in 1 files
    customer_data_failover_replica: seen in 1 files
    search_documents_primary      : seen in 1 files

### 7. JSON Files Analysis (.json under evidence/records/)
  Found 28 JSON files.
  - connector_configurations_20260812.json: Top-level keys: ['exported_at', 'origin', 'record_count', 'records']
  - customer_analytics_report_20260907.json: Top-level keys: ['captured_at', 'source', 'collection', 'records']
  - customer_data_snapshot_bundle_20260131.json: Top-level keys: ['exported_at', 'source', 'snapshots']
  - customer_data_snapshot_bundle_20260223.json: Top-level keys: ['exported_at', 'source', 'snapshots']
  - customer_data_snapshot_bundle_20260322.json: Top-level keys: ['exported_at', 'source', 'snapshots']
  - customer_data_snapshot_bundle_20260416.json: Top-level keys: ['exported_at', 'source', 'snapshots']
  - customer_data_snapshot_bundle_20260511.json: Top-level keys: ['exported_at', 'source', 'snapshots']
  - customer_data_snapshot_bundle_20260605.json: Top-level keys: ['exported_at', 'source', 'snapshots']
  - customer_data_snapshot_bundle_20260630.json: Top-level keys: ['exported_at', 'source', 'snapshots']
  - customer_data_snapshot_bundle_20260725.json: Top-level keys: ['exported_at', 'source', 'snapshots']
  - customer_data_snapshot_bundle_20260819.json: Top-level keys: ['exported_at', 'source', 'snapshots']
  - customer_data_snapshot_bundle_20260913.json: Top-level keys: ['exported_at', 'source', 'snapshots']
  - customer_data_snapshot_bundle_20260915.json: Top-level keys: ['exported_at', 'source', 'snapshots']
  - customer_data_snapshot_bundle_20260917.json: Top-level keys: ['exported_at', 'source', 'snapshots']
  - customer_export_jobs_20260914.json: Top-level keys: ['captured_at', 'source', 'collection', 'records']
  - customer_export_manifest_20260409.json: Top-level keys: ['exported_at', 'origin', 'record_count', 'records']
  - security_audit_ledger_20261001.json: Top-level keys: ['exported_at', 'origin', 'record_count', 'records']
  - service_resource_export_20260129_114459.json: Top-level keys: ['exported_at', 'region', 'service_exports', 'source']
  - service_resource_export_20260228_103637.json: Top-level keys: ['exported_at', 'region', 'service_exports', 'source']
  - service_resource_export_20260320_072349.json: Top-level keys: ['exported_at', 'region', 'service_exports', 'source']
  - service_resource_export_20260429_083222.json: Top-level keys: ['exported_at', 'region', 'service_exports', 'source']
  - service_resource_export_20260514_114454.json: Top-level keys: ['exported_at', 'region', 'service_exports', 'source']
  - service_resource_export_20260603_083457.json: Top-level keys: ['exported_at', 'region', 'service_exports', 'source']
  - service_resource_export_20260628_062556.json: Top-level keys: ['exported_at', 'region', 'service_exports', 'source']
  - service_resource_export_20260718_104335.json: Top-level keys: ['exported_at', 'region', 'service_exports', 'source']
  - service_resource_export_20260807_074104.json: Top-level keys: ['exported_at', 'region', 'service_exports', 'source']
  - service_resource_export_20260901_053316.json: Top-level keys: ['exported_at', 'region', 'service_exports', 'source']
  - service_resource_export_20260915_114455.json: Top-level keys: ['exported_at', 'region', 'service_exports', 'source']

  Unique dictionary shapes containing 'resource_id' (22 shapes):
    ('document', 'index_name', 'resource_id')
    ('hits', 'observed_at', 'query', 'resource_id')
    ('observed_at', 'profile', 'resource_id', 'status_code')
    ('archive_path', 'encryption', 'resource_id', 'restore_allowed', 'subject_reference')
    ('order_reference', 'resource_id', 'retained_until', 'retention_reason', 'subject_reference')
    ('actor_type', 'event_name', 'integrity_seal', 'resource_id', 'subject_reference')
    ('file_name', 'resource_id', 'storage_class', 'ticket_id', 'uploaded_by')
    ('channel', 'message_text', 'resource_id', 'subject_reference', 'ticket_id')
    ('event_code', 'observed_at', 'resource_id', 'retention_until', 'subject_reference')
    ('archive_key', 'customer_email', 'customer_reference', 'observed_at', 'resource_id', 'restore_allowed')
    ('connector_name', 'destination', 'enabled', 'mode', 'resource_id', 'subject_selector')
    ('record_type', 'recorded_at', 'resource_id', 'result', 'subject_reference', 'system')
    ('customer_reference', 'display_name', 'email', 'email_hash', 'phone', 'resource_id')
    ('customer_reference', 'object_key', 'observed_at', 'owner_email', 'owner_phone', 'resource_id')
    ('lookup_value', 'record_type', 'recorded_at', 'resource_id', 'result', 'system')
    ('customer_reference', 'message_excerpt', 'observed_at', 'requester_email', 'requester_name', 'requester_phone', 'resource_id')
    ('created_at', 'download_available', 'expires_at', 'file_name', 'included_sections', 'owner_email', 'resource_id')
    ('connector_name', 'customer_email', 'customer_reference', 'enabled', 'last_delivery_status', 'observed_at', 'resource_id')
    ('audience_cohort', 'customer_reference', 'email', 'email_hash', 'observed_at', 'phone', 'resource_id')
    ('account_status', 'customer_reference', 'email', 'full_name', 'phone', 'resource_id', 'signup_channel')
    ('account_status', 'email', 'email_hash', 'name', 'phone', 'resource_id', 'subject_reference')
    ('email', 'email_hash', 'metrics', 'phone', 'recent_activity', 'reporting_window', 'resource_id', 'user_id')

  Status/Result key-value counts observed in JSON:
    result = FOUND: 125
    enabled = True: 47
    result = NOT_FOUND: 43
    account_status = ACTIVE: 25
    restore_allowed = False: 25
    enabled = False: 25
    result = IDENTIFIABLE: 24
    result = ACTIVE: 16
    restore_allowed = True: 10
    result = ANONYMIZED: 9
    result = BLOCKED: 4
    result = DISABLED: 4
    result = REDACTED: 4
    account_status = DELETED: 2

### 8. Log Files Analysis (.log under evidence/logs/)
  Found 26 LOG files.
  - application_trace_ap_northeast_20260730.log: services=set(), events=set()
  - application_trace_eu_north_20260302.log: services=set(), events=set()
  - cloud_runtime_export_af_south_20260930.log: services=set(), events={'\\"export_started\\', '\\"telemetry_flushed\\', '\\"lease_extended\\', '\\"delivery_abandoned\\', '\\"profile_lookup_completed\\', '\\"cache_refresh\\'}
  - cloud_runtime_export_us_west_20260608.log: services=set(), events={'\\"restore_authorization_completed\\', '\\"dependency_retry\\', '\\"message_scan_started\\', '\\"connection_acquired\\', '\\"message_read\\', '\\"message_pii_scan\\', '\\"export_started\\', '\\"index_query_completed\\', '\\"dependency_recovered\\', '\\"attachment_scan_started\\', '\\"attachment_pii_scan\\', '\\"audit_record_query_started\\', '\\"connector_heartbeat\\', '\\"analytics_profile_scan_started\\', '\\"connector_config_loaded\\', '\\"telemetry_flushed\\', '\\"lease_extended\\', '\\"cache_refresh\\', '\\"cache_lookup\\', '\\"profile_lookup_started\\', '\\"profile_lookup_completed\\', '\\"audit_record_read_completed\\', '\\"index_query_started\\', '\\"delivery_abandoned\\', '\\"analytics_profile_read\\', '\\"connector_config_read_started\\', '\\"analytics_identity_scan\\', '\\"restore_policy_check_started\\'}
  - notification_delivery_20260315.log: services={'downstream_delivery_service'}, events={'record_lookup'}
  - operations_stream_eu_central_20260705.log: services=set(), events=set()
  - operations_stream_me_central_20260203.log: services=set(), events=set()
  - resource_lookup_trace_20260218_083911.log: services={'account_service', 'backup_service', 'readback_collector', 'search_service', 'security_service', 'export_service', 'analytics_platform', 'integration_service', 'support_platform'}, events={'analytics_profile_read_started', 'export_metadata_read_started', 'index_query_completed', 'audit_record_read_started', 'analytics_profile_read_completed', 'restore_policy_read_started', 'support_ticket_read_started', 'profile_lookup_started', 'restore_policy_read_completed', 'support_ticket_read_completed', 'audit_record_read_completed', 'export_completed', 'connector_config_read_started', 'profile_lookup_completed', 'index_query_started', 'connector_config_read_completed', 'export_metadata_read_completed', 'export_started'}
  - resource_lookup_trace_20260310_061801.log: services={'readback_collector', 'account_service'}, events={'profile_lookup_completed', 'profile_lookup_started', 'export_completed', 'export_started'}
  - resource_lookup_trace_20260414_054007.log: services={'account_service', 'readback_collector', 'search_service', 'security_service', 'analytics_platform', 'integration_service', 'support_platform'}, events={'analytics_profile_read_started', 'audit_record_read_started', 'index_query_completed', 'analytics_profile_read_completed', 'support_ticket_read_started', 'profile_lookup_started', 'export_completed', 'support_ticket_read_completed', 'audit_record_read_completed', 'connector_config_read_started', 'profile_lookup_completed', 'index_query_started', 'connector_config_read_completed', 'export_started'}
  - resource_lookup_trace_20260509_104353.log: services={'account_service', 'backup_service', 'readback_collector', 'search_service', 'security_service', 'analytics_platform', 'integration_service', 'support_platform'}, events={'analytics_profile_read_started', 'audit_record_read_started', 'index_query_completed', 'restore_policy_read_started', 'analytics_profile_read_completed', 'export_started', 'profile_lookup_started', 'index_query_started', 'support_ticket_read_completed', 'restore_policy_read_completed', 'export_completed', 'connector_config_read_started', 'profile_lookup_completed', 'support_ticket_read_started', 'connector_config_read_completed', 'audit_record_read_completed'}
  - resource_lookup_trace_20260529_074313.log: services={'account_service', 'backup_service', 'readback_collector', 'search_service', 'security_service', 'export_service', 'analytics_platform', 'integration_service', 'support_platform'}, events={'restore_policy_read_started', 'audit_record_read_started', 'index_query_completed', 'export_metadata_read_started', 'analytics_profile_read_started', 'analytics_profile_read_completed', 'profile_lookup_started', 'index_query_started', 'restore_policy_read_completed', 'support_ticket_read_completed', 'audit_record_read_completed', 'export_completed', 'connector_config_read_started', 'profile_lookup_completed', 'support_ticket_read_started', 'connector_config_read_completed', 'export_metadata_read_completed', 'export_started'}
  - resource_lookup_trace_20260623_053726.log: services={'account_service', 'backup_service', 'readback_collector', 'search_service', 'security_service', 'analytics_platform', 'export_service', 'integration_service', 'support_platform'}, events={'analytics_profile_read_started', 'audit_record_read_started', 'index_query_completed', 'restore_policy_read_started', 'analytics_profile_read_completed', 'connector_config_read_started', 'export_metadata_read_started', 'support_ticket_read_started', 'profile_lookup_started', 'restore_policy_read_completed', 'support_ticket_read_completed', 'export_completed', 'audit_record_read_completed', 'profile_lookup_completed', 'index_query_started', 'connector_config_read_completed', 'export_metadata_read_completed', 'export_started'}
  - resource_lookup_trace_20260713_093359.log: services={'account_service', 'readback_collector', 'search_service', 'security_service', 'analytics_platform', 'integration_service', 'support_platform'}, events={'analytics_profile_read_started', 'audit_record_read_started', 'connector_config_read_started', 'index_query_completed', 'analytics_profile_read_completed', 'support_ticket_read_started', 'profile_lookup_started', 'export_completed', 'support_ticket_read_completed', 'audit_record_read_completed', 'profile_lookup_completed', 'index_query_started', 'connector_config_read_completed', 'export_started'}
  - resource_lookup_trace_20260728_054417.log: services={'account_service', 'backup_service', 'readback_collector', 'search_service', 'security_service', 'analytics_platform', 'export_service', 'integration_service', 'support_platform'}, events={'analytics_profile_read_started', 'export_metadata_read_started', 'index_query_completed', 'audit_record_read_started', 'analytics_profile_read_completed', 'connector_config_read_started', 'restore_policy_read_started', 'support_ticket_read_started', 'profile_lookup_started', 'restore_policy_read_completed', 'support_ticket_read_completed', 'audit_record_read_completed', 'export_completed', 'export_metadata_read_completed', 'profile_lookup_completed', 'index_query_started', 'connector_config_read_completed', 'export_started'}
  - resource_lookup_trace_20260822_103910.log: services={'account_service', 'readback_collector', 'search_service', 'security_service', 'export_service', 'analytics_platform', 'integration_service', 'support_platform'}, events={'export_metadata_read_started', 'audit_record_read_started', 'index_query_completed', 'analytics_profile_read_started', 'analytics_profile_read_completed', 'support_ticket_read_started', 'profile_lookup_started', 'export_completed', 'support_ticket_read_completed', 'audit_record_read_completed', 'connector_config_read_started', 'profile_lookup_completed', 'index_query_started', 'connector_config_read_completed', 'export_metadata_read_completed', 'export_started'}
  - resource_lookup_trace_20260911_074253.log: services={'account_service', 'backup_service', 'readback_collector', 'search_service', 'security_service', 'analytics_platform', 'integration_service', 'support_platform'}, events={'analytics_profile_read_started', 'audit_record_read_started', 'connector_config_read_started', 'restore_policy_read_started', 'analytics_profile_read_completed', 'index_query_completed', 'profile_lookup_started', 'index_query_started', 'restore_policy_read_completed', 'support_ticket_read_completed', 'export_completed', 'audit_record_read_completed', 'profile_lookup_completed', 'support_ticket_read_started', 'connector_config_read_completed', 'export_started'}
  - resource_lookup_trace_20260926_103856.log: services={'account_service', 'backup_service', 'readback_collector', 'search_service', 'security_service', 'analytics_platform', 'integration_service', 'support_platform'}, events={'restore_policy_read_started', 'audit_record_read_started', 'index_query_completed', 'analytics_profile_read_started', 'analytics_profile_read_completed', 'support_ticket_read_started', 'profile_lookup_started', 'restore_policy_read_completed', 'support_ticket_read_completed', 'audit_record_read_completed', 'export_completed', 'connector_config_read_started', 'profile_lookup_completed', 'index_query_started', 'connector_config_read_completed', 'export_started'}
  - search_index_diagnostic_20260906.log: services={'search_index_service'}, events={'record_lookup'}
  - service_events_ap_south_20260915.log: services={'account_service', 'webhook_delivery', 'log_router', 'backup_service', 'search_service', 'secret_agent', 'security_service', 'queue_consumer', 'integration_service', 'analytics_platform', 'export_service', 'dns_cache', 'support_platform'}, events={'restore_policy_check_started', 'dependency_recovered', 'connection_acquired', 'export_download_check_completed', 'contact_lookup_completed', 'audit_record_query_started', 'cache_refresh', 'lease_extended', 'export_started', 'message_pii_scan', 'export_completed', 'connector_config_read_started', 'profile_lookup_completed', 'restore_candidate_evaluated', 'message_scan_started', 'profile_lookup_started', 'index_query_started', 'audit_record_read_completed', 'delivery_abandoned', 'connector_heartbeat', 'export_download_check_started', 'index_query_completed', 'analytics_identity_scan', 'cache_lookup', 'consumer_lag', 'dependency_retry', 'attachment_pii_scan', 'attachment_scan_started', 'analytics_profile_scan_started'}
  - service_events_sa_east_20260516.log: services={'account_service', 'backup_service', 'webhook_delivery', 'log_router', 'search_service', 'dns_cache', 'secret_agent', 'security_service', 'queue_consumer', 'analytics_platform', 'integration_service', 'support_platform'}, events={'connection_acquired', 'dependency_recovered', 'audit_record_query_started', 'cache_refresh', 'lease_extended', 'message_pii_scan', 'export_completed', 'connector_config_read_started', 'profile_lookup_completed', 'analytics_profile_read', 'restore_candidate_evaluated', 'message_scan_started', 'profile_lookup_started', 'audit_record_read_completed', 'delivery_abandoned', 'connector_heartbeat', 'index_query_completed', 'analytics_identity_scan', 'cache_lookup', 'consumer_lag', 'dependency_retry', 'index_query_started', 'analytics_profile_scan_started'}
  - structured_service_events_ca_central_20260419.log: services=set(), events=set()
  - structured_service_events_eu_west_20260918.log: services=set(), events=set()
  - support_replica.log: services={'attachment_preview', 'queue_consumer', 'support_replica'}, events={'deletion_marker_check', 'thumbnail_failed', 'contact_query_completed', 'contact_query_started', 'consumer_lag', 'checkpoint_saved', 'batch_started'}
  - syslog_archive_ap_southeast_20260325.log: services=set(), events={'connection_acquired', 'dependency_recovered', 'export_download_check_completed', 'audit_record_query_started', 'cache_refresh', 'message_pii_scan', 'connector_config_read_started', 'profile_lookup_completed', 'attachment_pii_scan', 'message_scan_started', 'profile_lookup_started', 'attachment_scan_started', 'certificate_checked', 'audit_record_read_completed', 'connector_heartbeat', 'timer_tick', 'index_query_completed', 'analytics_identity_scan', 'disk_latency', 'cache_lookup', 'dependency_retry', 'index_query_started', 'export_started', 'analytics_profile_scan_started'}
  - syslog_archive_us_east_20260824.log: services=set(), events={'connection_acquired', 'dependency_recovered', 'export_download_check_completed', 'audit_record_query_started', 'cache_refresh', 'message_pii_scan', 'connector_config_read_started', 'profile_lookup_completed', 'analytics_profile_read', 'attachment_pii_scan', 'message_scan_started', 'profile_lookup_started', 'certificate_checked', 'audit_record_read_completed', 'connector_heartbeat', 'timer_tick', 'export_download_check_started', 'index_query_completed', 'disk_latency', 'cache_lookup', 'dependency_retry', 'index_query_started', 'attachment_scan_started', 'analytics_profile_scan_started'}

  Top event= values across all log files:
    \"profile_lookup_completed\        : 310
    profile_lookup_completed           : 91
    profile_lookup_started             : 81
    index_query_completed              : 80
    audit_record_read_completed        : 77
    record_lookup                      : 75
    index_query_started                : 72
    connection_acquired                : 65
    connector_config_read_started      : 42
    analytics_profile_read_started     : 39
    analytics_profile_read_completed   : 39
    audit_record_read_started          : 37
    connector_config_read_completed    : 34
    support_ticket_read_started        : 34
    support_ticket_read_completed      : 34
    cache_lookup                       : 34
    audit_record_query_started         : 32
    dependency_retry                   : 31
    dependency_recovered               : 31
    \"connection_acquired\             : 16
    restore_policy_read_started        : 15
    restore_policy_read_completed      : 15
    export_started                     : 13
    export_completed                   : 13
    \"cache_lookup\                    : 11
    \"profile_lookup_started\          : 10
    \"dependency_retry\                : 10
    \"dependency_recovered\            : 10
    \"audit_record_read_completed\     : 10
    connector_heartbeat                : 10
    message_pii_scan                   : 9
    \"index_query_completed\           : 8
    analytics_profile_scan_started     : 8
    \"audit_record_query_started\      : 7
    message_scan_started               : 7
    analytics_profile_read             : 6
    \"index_query_started\             : 5
    export_metadata_read_started       : 5
    export_metadata_read_completed     : 5
    \"message_scan_started\            : 4
    \"message_pii_scan\                : 4
    cache_refresh                      : 4
    analytics_identity_scan            : 4
    \"connector_config_read_started\   : 3
    \"connector_heartbeat\             : 3
    consumer_lag                       : 3
    attachment_scan_started            : 3
    attachment_pii_scan                : 3
    restore_candidate_evaluated        : 3
    export_download_check_completed    : 3
    contact_query_completed            : 3
    \"export_started\                  : 2
    \"cache_refresh\                   : 2
    \"lease_extended\                  : 2
    \"delivery_abandoned\              : 2
    \"telemetry_flushed\               : 2
    \"analytics_profile_scan_started\  : 2
    \"analytics_identity_scan\         : 2
    \"analytics_profile_read\          : 2
    lease_extended                     : 2
    delivery_abandoned                 : 2
    restore_policy_check_started       : 2
    export_download_check_started      : 2
    contact_query_started              : 2
    timer_tick                         : 2
    certificate_checked                : 2
    disk_latency                       : 2
    \"message_read\                    : 1
    \"attachment_scan_started\         : 1
    \"attachment_pii_scan\             : 1
    \"restore_policy_check_started\    : 1
    \"restore_authorization_completed\ : 1
    \"connector_config_loaded\         : 1
    contact_lookup_completed           : 1
    batch_started                      : 1
    deletion_marker_check              : 1
    thumbnail_failed                   : 1
    checkpoint_saved                   : 1

  Top service= values across all log files:
    account_service               : 155
    security_service              : 129
    search_service                : 127
    analytics_platform            : 99
    integration_service           : 85
    support_platform              : 84
    downstream_delivery_service   : 39
    backup_service                : 39
    search_index_service          : 36
    readback_collector            : 22
    export_service                : 13
    support_replica               : 8
    log_router                    : 3
    queue_consumer                : 3
    dns_cache                     : 2
    secret_agent                  : 2
    webhook_delivery              : 2
    attachment_preview            : 1

### 9. PDF Files Analysis (.pdf under evidence/documents/)
  Found 4 PDF files.

--- PDF: account_history_report_20260718.pdf ---
  [pypdf] Pages: 2
  Showing up to 40 lines from account_history_report_20260718.pdf:
    [01] NORTHSTAR SHOP - CUSTOMER STATEMENT
    [02] Statement NST-2026-0718-1842
    [03] Customer and order
    [04] Record
    [05] Customer Ingrid Dahl
    [06] Detail
    [07] user_18
    [08] Detail
    [09] ingrid.dahl@outlook.com
    [10] Detail
    [11] statement NST-2026-0718-1842
    [12] Detail
    [13] order ORD-20261260
    [14] Item
    [15] Smart desk lamp, SKU LAMP-SD-04, quantity 1, subtotal EUR 54.95, shipping EUR 4.99, tax
    [16] EUR 11.99, total EUR 71.93
    [17] Record
    [18] Payment Visa ending 4821
    [19] Detail
    [20] billing status paid
    [21] Detail
    [22] order date 08 Jul 2026
    [23] Detail
    [24] dispatched 10 Jul
    [25] Detail
    [26] delivered 14 Jul
    [27] 
    [28] NORTHSTAR SHOP - CUSTOMER STATEMENT
    [29] Continued - Order timeline and returns
    [30] Charges and delivery
    [31] Delivery address
    [32] 24 Fjordgata, 7010 Trondheim, Norway
    [33] Timeline
    [34] order placed, payment authorised, warehouse packed, carrier collected, delivered
    [35] 

--- PDF: delivery_correction_attachment.pdf ---
  [pypdf] Pages: 2
  Showing up to 40 lines from delivery_correction_attachment.pdf:
    [01] DELIVERY ADDRESS CORRECTION REQUEST
    [02] Support reference CS-4827 / support_001
    [03] Customer request
    [04] Record
    [05] Northstar Shop Delivery Address Correction Request
    [06] Detail
    [07] reference CS-4827 / support_001
    [08] Detail
    [09] received 18 Jun 2026
    [10] Detail
    [11] Priya Raman
    [12] Detail
    [13] priya.raman@gmail.com
    [14] Detail
    [15] +91 98765 73142
    [16] Detail
    [17] order ORD-20264827
    [18] Detail
    [19] preferred contact SMS
    [20] submitted 18 Jun 2026 10
    [21] 24 UTC
    [22] Customer request
    [23] change apartment number from 14B to 18B and call before delivery
    [24] Product
    [25] Stainless steel water bottle, quantity 2
    [26] Detail
    [27] carrier SwiftShip
    [28] 
    [29] DELIVERY ADDRESS CORRECTION REQUEST
    [30] Continued - Attachment properties and upload history
    [31] Order and delivery details
    [32] Record
    [33] file delivery_address_correction.pdf
    [34] Detail
    [35] 312 KB
    [36] Detail
    [37] ticket CS-4827
    [38] Detail
    [39] region ap-south
    [40] Detail

--- PDF: legal_retention_register_20260529.pdf ---
  [pypdf] Pages: 2
  Showing up to 40 lines from legal_retention_register_20260529.pdf:
    [01] DISPUTED ORDERS AND TAX RECORDS REGISTER
    [02] Finance Operations | May 2026
    [03] Register details
    [04] Record
    [05] Register month May 2026
    [06] Detail
    [07] owner Finance Records
    [08] Detail
    [09] classification Internal
    [10] generated 29 May 2026 08
    [11] 00 UTC
    [12] Detail
    [13] For each row add invoice date, finance owner, retain-until date, and case/reference number
    [14] 
    [15] DISPUTED ORDERS AND TAX RECORDS REGISTER
    [16] Continued - Review and custody notes
    [17] Disputed order entries
    [18] 1
    [19] ORD-20264118 | user_08 | Card dispute | 04 May 2026 | USD 184.20 | Retain until 04 May 2033 | AR
    [20] 2
    [21] ORD-20264207 | user_12 | Tax correction | 09 May 2026 | EUR 72.40 | Retain until 09 May 2033 | ML
    [22] 3
    [23] ORD-20264319 | user_17 | Chargeback | 14 May 2026 | GBP 219.00 | Retain until 14 May 2033 | SK
    [24] 4
    [25] ORD-20264402 | user_21 | Invoice inquiry | 18 May 2026 | CAD 96.55 | Retain until 18 May 2033 | AR
    [26] 5
    [27] ORD-20264511 | user_24 | Card dispute | 23 May 2026 | AUD 311.80 | Retain until 23 May 2033 | ML
    [28] 6
    [29] ORD-20264600 | user_29 | Tax record | 28 May 2026 | USD 48.75 | Retain until 28 May 2033 | SK
    [30] 

--- PDF: security_retention_extract.pdf ---
  [pypdf] Pages: 1
  Showing up to 40 lines from security_retention_extract.pdf:
    [01] COMPLIANCE JOURNAL - SIGNED RECORD EXTRACT
    [02] Reference CJX-20260905-0630
    [03] Journal entry
    [04] Record
    [05] Product Northstar Shop Compliance Journal
    [06] Detail
    [07] classification Internal Restricted
    [08] Detail
    [09] reference CJX-20260905-0630
    [10] issued 05 Sep 2026 06
    [11] 30 UTC
    [12] Record
    [13] Event reference audit_record_003
    [14] Detail
    [15] subject reference user_03
    [16] Detail
    [17] event Account closure recorded
    [18] Detail
    [19] actor automated account workflow
    [20] recorded 25 Aug 2026 04
    [21] 03 UTC
    [22] retain until 25 Aug 2027 04
    [23] 03 UTC
    [24] Record
    [25] Journal partition 2026-Q3
    [26] Detail
    [27] record version 1
    [28] Detail
    [29] storage class compliance-ledger
    [30] Detail
    [31] integrity seal valid
    [32] Detail
    [33] short fingerprint 8f0c…31ad
    [34] 

### 10. Deletion Rules (deletion_rules.csv)
  - rule_01 | USER_PROFILE           | DELETE     | Condition: Always
  - rule_02 | SECONDARY_IDENTIFIER   | DELETE     | Condition: Always
  - rule_03 | SEARCH_INDEX_ENTRY     | DELETE     | Condition: Always
  - rule_04 | CACHE_ENTRY            | DELETE     | Condition: Always
  - rule_05 | SUPPORT_MESSAGE        | REDACT     | Condition: Conversation contains shared customer, agent, or order context that must be retained
  - rule_06 | SUPPORT_ATTACHMENT     | DELETE     | Condition: Attachment belongs only to the deletion subject
  - rule_07 | ANALYTICS_PROFILE      | ANONYMIZE  | Condition: Record is still attributable to a user
  - rule_08 | PRODUCT_TELEMETRY      | ANONYMIZE  | Condition: Record is still attributable to a user
  - rule_09 | USER_EXPORT            | DELETE     | Condition: Always
  - rule_10 | MARKETING_PROFILE      | DELETE     | Condition: Always
  - rule_11 | EMAIL_DELIVERY_LOG     | REDACT     | Condition: Log contains a user email address
  - rule_12 | SECURITY_AUDIT_LOG     | RETAIN     | Condition: Record is within the supplied retention period
  - rule_13 | LEGAL_HOLD_RECORD      | RETAIN     | Condition: A supplied legal hold is active
  - rule_14 | BACKUP_ARCHIVE         | RETAIN     | Condition: Restore access can be blocked
  - rule_15 | ACCOUNT_TOMBSTONE      | REDACT     | Condition: Account is deleted and only a stable internal user_id is needed to preserve references to retained records
