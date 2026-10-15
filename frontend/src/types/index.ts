export type UserRole = 'super_admin' | 'engineer' | 'viewer';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  full_name: string;
  role: UserRole;
}

export type LogSeverity = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

export interface LogEntry {
  id: string;
  service_id: string;
  service_name: string;
  environment: string;
  severity: LogSeverity;
  message: string;
  timestamp: string;
  source?: string;
  trace_id?: string;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface LogListResponse {
  items: LogEntry[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export type IncidentStatus = 'OPEN' | 'ACKNOWLEDGED' | 'INVESTIGATING' | 'RESOLVED';
export type IncidentSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Incident {
  id: string;
  title: string;
  description?: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  service_id: string;
  service_name?: string;
  environment: string;
  rule_id?: string;
  rule_name?: string;
  fingerprint: string;
  error_signature?: string;
  first_detected_at: string;
  last_detected_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  assigned_user_id?: string;
  assigned_user_name?: string;
  event_count: number;
  created_at: string;
  updated_at: string;
}

export interface IncidentComment {
  id: string;
  incident_id: string;
  user_id: string;
  user_name?: string;
  user_email?: string;
  comment: string;
  created_at: string;
}

export interface IncidentEvent {
  id: string;
  incident_id: string;
  event_type: string;
  actor_id?: string;
  actor_name: string;
  details_json?: Record<string, any>;
  created_at: string;
}

export interface IncidentDetail extends Incident {
  comments: IncidentComment[];
  timeline: IncidentEvent[];
  related_logs: LogEntry[];
}

export type RuleType = 'error_threshold' | 'critical_log' | 'repeated_failure' | 'error_rate' | 'service_inactivity';

export interface DetectionRule {
  id: string;
  name: string;
  description?: string;
  rule_type: RuleType;
  severity: IncidentSeverity;
  service_id?: string;
  environment?: string;
  threshold: number;
  time_window_seconds: number;
  cooldown_seconds: number;
  error_signature_pattern?: string;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ServiceItem {
  id: string;
  name: string;
  description?: string;
  environment: string;
  owner_team: string;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
  last_log_at?: string;
  health_status: 'HEALTHY' | 'DEGRADED' | 'CRITICAL' | 'UNKNOWN';
  active_incidents_count: number;
  recent_error_count: number;
  total_logs_count: number;
}

export interface IngestionKey {
  id: string;
  service_id: string;
  key_name: string;
  key_prefix: string;
  is_revoked: boolean;
  created_at: string;
  last_used_at?: string;
  raw_key?: string;
}

export interface AlertItem {
  id: string;
  incident_id?: string;
  title: string;
  message: string;
  severity: IncidentSeverity;
  is_read: boolean;
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  actor_email: string;
  actor_role: string;
  action: string;
  target_type: string;
  target_id?: string;
  correlation_id?: string;
  details_json?: Record<string, any>;
  ip_address?: string;
  created_at: string;
}

export interface DashboardSummaryData {
  total_logs: number;
  error_logs: number;
  active_incidents: number;
  critical_incidents: number;
  healthy_services: number;
  total_services: number;
  unacknowledged_alerts: number;
}

export interface DashboardAllData {
  summary: DashboardSummaryData;
  log_volume: { timestamp: string; count: number; errors: number }[];
  severity_breakdown: { severity: string; count: number }[];
  incident_trends: { date: string; opened: number; resolved: number }[];
  incidents_by_service: { service_name: string; incident_count: number }[];
  service_health: {
    service_id: string;
    service_name: string;
    environment: string;
    status: string;
    active_incidents: number;
    error_count_last_hour: number;
    last_log_at?: string;
  }[];
}
