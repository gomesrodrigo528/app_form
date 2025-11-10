-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.form_fields (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  form_id uuid NOT NULL,
  field_type character varying NOT NULL,
  label character varying NOT NULL,
  placeholder character varying,
  is_required boolean DEFAULT false,
  field_order integer NOT NULL,
  options jsonb,
  validation_rules jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  is_multiple boolean DEFAULT false,
  CONSTRAINT form_fields_pkey PRIMARY KEY (id),
  CONSTRAINT form_fields_form_id_fkey FOREIGN KEY (form_id) REFERENCES public.forms(id)
);
CREATE TABLE public.form_responses (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  submission_id uuid NOT NULL,
  field_id uuid NOT NULL,
  response_value text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT form_responses_pkey PRIMARY KEY (id),
  CONSTRAINT form_responses_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.form_submissions(id),
  CONSTRAINT form_responses_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.form_fields(id)
);
CREATE TABLE public.form_submissions (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  form_id uuid NOT NULL,
  lead_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  status character varying DEFAULT 'incomplete'::character varying,
  started_at timestamp with time zone DEFAULT now(),
  completed_at timestamp with time zone,
  whatsapp_sent boolean DEFAULT false,
  whatsapp_sent_at timestamp with time zone,
  CONSTRAINT form_submissions_pkey PRIMARY KEY (id),
  CONSTRAINT form_submissions_form_id_fkey FOREIGN KEY (form_id) REFERENCES public.forms(id),
  CONSTRAINT form_submissions_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id),
  CONSTRAINT form_submissions_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
);
CREATE TABLE public.forms (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  title character varying NOT NULL,
  description text,
  is_active boolean DEFAULT true,
  created_by uuid,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT forms_pkey PRIMARY KEY (id),
  CONSTRAINT forms_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id),
  CONSTRAINT forms_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id)
);
CREATE TABLE public.leads (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  phone character varying,
  email character varying,
  name character varying,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT leads_pkey PRIMARY KEY (id),
  CONSTRAINT leads_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
);
CREATE TABLE public.schema_versions (
  id integer NOT NULL DEFAULT nextval('schema_versions_id_seq'::regclass),
  name character varying NOT NULL UNIQUE,
  version integer NOT NULL,
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT schema_versions_pkey PRIMARY KEY (id)
);
CREATE TABLE public.tenant_audit_log (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  tenant_id uuid,
  admin_user_id uuid,
  action character varying NOT NULL,
  changes jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT tenant_audit_log_pkey PRIMARY KEY (id),
  CONSTRAINT tenant_audit_log_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id),
  CONSTRAINT tenant_audit_log_admin_user_id_fkey FOREIGN KEY (admin_user_id) REFERENCES public.users(id)
);
CREATE TABLE public.tenant_settings (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL UNIQUE,
  welcome_message text,
  thank_you_message text,
  custom_css text,
  redirect_after_submit boolean DEFAULT true,
  allow_multiple_submissions boolean DEFAULT false,
  settings jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT tenant_settings_pkey PRIMARY KEY (id),
  CONSTRAINT tenant_settings_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
);
CREATE TABLE public.tenants (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  name character varying NOT NULL,
  slug character varying NOT NULL UNIQUE,
  whatsapp_number character varying,
  primary_color character varying DEFAULT '#3B82F6'::character varying,
  secondary_color character varying DEFAULT '#1E40AF'::character varying,
  logo_url text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  is_active boolean DEFAULT true,
  owner_email character varying,
  CONSTRAINT tenants_pkey PRIMARY KEY (id)
);
CREATE TABLE public.users (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  email character varying NOT NULL UNIQUE,
  password_hash character varying NOT NULL,
  full_name character varying NOT NULL,
  role character varying DEFAULT 'user'::character varying,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  last_login timestamp with time zone,
  is_superuser boolean DEFAULT false,
  CONSTRAINT users_pkey PRIMARY KEY (id),
  CONSTRAINT users_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
);