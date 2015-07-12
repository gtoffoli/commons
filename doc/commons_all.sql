BEGIN;
CREATE TABLE "commons_materialentry" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL UNIQUE,
    "order" integer NOT NULL
)
;
CREATE TABLE "commons_mediaentry" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL UNIQUE,
    "order" integer NOT NULL
)
;
CREATE TABLE "commons_accessibilityentry" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL UNIQUE,
    "order" integer NOT NULL
)
;
CREATE TABLE "commons_levelnode" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL UNIQUE,
    "order" integer NOT NULL,
    "parent_id" integer REFERENCES "commons_levelnode" ("id") DEFERRABLE INITIALLY DEFERRED,
    "lft" integer CHECK ("lft" >= 0) NOT NULL,
    "rght" integer CHECK ("rght" >= 0) NOT NULL,
    "tree_id" integer CHECK ("tree_id" >= 0) NOT NULL,
    "level" integer CHECK ("level" >= 0) NOT NULL
)
;
CREATE TABLE "commons_subjectnode" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL UNIQUE,
    "order" integer NOT NULL,
    "parent_id" integer REFERENCES "commons_subjectnode" ("id") DEFERRABLE INITIALLY DEFERRED,
    "lft" integer CHECK ("lft" >= 0) NOT NULL,
    "rght" integer CHECK ("rght" >= 0) NOT NULL,
    "tree_id" integer CHECK ("tree_id" >= 0) NOT NULL,
    "level" integer CHECK ("level" >= 0) NOT NULL
)
;
CREATE TABLE "commons_licensenode" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL UNIQUE,
    "order" integer NOT NULL,
    "parent_id" integer REFERENCES "commons_licensenode" ("id") DEFERRABLE INITIALLY DEFERRED,
    "lft" integer CHECK ("lft" >= 0) NOT NULL,
    "rght" integer CHECK ("rght" >= 0) NOT NULL,
    "tree_id" integer CHECK ("tree_id" >= 0) NOT NULL,
    "level" integer CHECK ("level" >= 0) NOT NULL
)
;
CREATE TABLE "commons_edulevelentry" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL UNIQUE,
    "order" integer NOT NULL
)
;
CREATE TABLE "commons_prostatusnode" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL UNIQUE,
    "order" integer NOT NULL,
    "parent_id" integer REFERENCES "commons_prostatusnode" ("id") DEFERRABLE INITIALLY DEFERRED,
    "lft" integer CHECK ("lft" >= 0) NOT NULL,
    "rght" integer CHECK ("rght" >= 0) NOT NULL,
    "tree_id" integer CHECK ("tree_id" >= 0) NOT NULL,
    "level" integer CHECK ("level" >= 0) NOT NULL
)
;
CREATE TABLE "commons_edufieldentry" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL UNIQUE,
    "order" integer NOT NULL
)
;
CREATE TABLE "commons_profieldentry" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL UNIQUE,
    "order" integer NOT NULL
)
;
CREATE TABLE "commons_networkentry" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL UNIQUE,
    "order" integer NOT NULL
)
;
CREATE TABLE "commons_language" (
    "code" varchar(5) NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL
)
;
CREATE TABLE "commons_countryentry" (
    "code" varchar(5) NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL
)
;
CREATE TABLE "commons_userprofile_languages" (
    "id" serial NOT NULL PRIMARY KEY,
    "userprofile_id" integer NOT NULL,
    "language_id" varchar(5) NOT NULL REFERENCES "commons_language" ("code") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("userprofile_id", "language_id")
)
;
CREATE TABLE "commons_userprofile_subjects" (
    "id" serial NOT NULL PRIMARY KEY,
    "userprofile_id" integer NOT NULL,
    "subjectnode_id" integer NOT NULL REFERENCES "commons_subjectnode" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("userprofile_id", "subjectnode_id")
)
;
CREATE TABLE "commons_userprofile_networks" (
    "id" serial NOT NULL PRIMARY KEY,
    "userprofile_id" integer NOT NULL,
    "networkentry_id" integer NOT NULL REFERENCES "commons_networkentry" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("userprofile_id", "networkentry_id")
)
;
CREATE TABLE "commons_userprofile" (
    "user_id" integer NOT NULL PRIMARY KEY REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "gender" varchar(1),
    "dob" date,
    "country_id" varchar(5) REFERENCES "commons_countryentry" ("code") DEFERRABLE INITIALLY DEFERRED,
    "city" varchar(250),
    "edu_level_id" integer REFERENCES "commons_edulevelentry" ("id") DEFERRABLE INITIALLY DEFERRED,
    "pro_status_id" integer REFERENCES "commons_prostatusnode" ("id") DEFERRABLE INITIALLY DEFERRED,
    "position" text,
    "edu_field_id" integer REFERENCES "commons_edufieldentry" ("id") DEFERRABLE INITIALLY DEFERRED,
    "pro_field_id" integer REFERENCES "commons_profieldentry" ("id") DEFERRABLE INITIALLY DEFERRED,
    "other_languages" text NOT NULL,
    "short" text NOT NULL,
    "long" text NOT NULL,
    "url" varchar(64) NOT NULL
)
;
ALTER TABLE "commons_userprofile_languages" ADD CONSTRAINT "userprofile_id_refs_user_id_5473925a" FOREIGN KEY ("userprofile_id") REFERENCES "commons_userprofile" ("user_id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "commons_userprofile_subjects" ADD CONSTRAINT "userprofile_id_refs_user_id_a3d7301e" FOREIGN KEY ("userprofile_id") REFERENCES "commons_userprofile" ("user_id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "commons_userprofile_networks" ADD CONSTRAINT "userprofile_id_refs_user_id_91924c2a" FOREIGN KEY ("userprofile_id") REFERENCES "commons_userprofile" ("user_id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "commons_subject" (
    "code" varchar(10) NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL
)
;
CREATE TABLE "commons_projtype" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(20) NOT NULL UNIQUE,
    "description" varchar(100) NOT NULL,
    "order" integer CHECK ("order" >= 0) NOT NULL
)
;
CREATE TABLE "commons_project" (
    "id" serial NOT NULL PRIMARY KEY,
    "group_id" integer NOT NULL UNIQUE REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(100) NOT NULL,
    "slug" varchar(50) NOT NULL UNIQUE,
    "proj_type_id" integer NOT NULL REFERENCES "commons_projtype" ("id") DEFERRABLE INITIALLY DEFERRED,
    "chat_type" integer,
    "description" text,
    "info" text,
    "state" integer,
    "created" timestamp with time zone NOT NULL,
    "modified" timestamp with time zone NOT NULL,
    "creator_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "editor_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "commons_projectmember" (
    "id" serial NOT NULL PRIMARY KEY,
    "project_id" integer NOT NULL REFERENCES "commons_project" ("id") DEFERRABLE INITIALLY DEFERRED,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "state" integer,
    "created" timestamp with time zone NOT NULL,
    "accepted" timestamp with time zone,
    "modified" timestamp with time zone NOT NULL,
    "editor_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "history" text
)
;
CREATE TABLE "commons_repofeature" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL,
    "order" integer CHECK ("order" >= 0) NOT NULL
)
;
CREATE TABLE "commons_repotype" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(20) NOT NULL UNIQUE,
    "description" varchar(100) NOT NULL,
    "order" integer CHECK ("order" >= 0) NOT NULL
)
;
CREATE TABLE "commons_repo_features" (
    "id" serial NOT NULL PRIMARY KEY,
    "repo_id" integer NOT NULL,
    "repofeature_id" integer NOT NULL REFERENCES "commons_repofeature" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("repo_id", "repofeature_id")
)
;
CREATE TABLE "commons_repo_languages" (
    "id" serial NOT NULL PRIMARY KEY,
    "repo_id" integer NOT NULL,
    "language_id" varchar(5) NOT NULL REFERENCES "commons_language" ("code") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("repo_id", "language_id")
)
;
CREATE TABLE "commons_repo_subjects" (
    "id" serial NOT NULL PRIMARY KEY,
    "repo_id" integer NOT NULL,
    "subjectnode_id" integer NOT NULL REFERENCES "commons_subjectnode" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("repo_id", "subjectnode_id")
)
;
CREATE TABLE "commons_repo" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(255) NOT NULL,
    "slug" varchar(50) NOT NULL UNIQUE,
    "repo_type_id" integer NOT NULL REFERENCES "commons_repotype" ("id") DEFERRABLE INITIALLY DEFERRED,
    "url" varchar(64),
    "description" text,
    "info" text,
    "eval" text,
    "state" integer,
    "created" timestamp with time zone NOT NULL,
    "modified" timestamp with time zone NOT NULL,
    "creator_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "editor_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
ALTER TABLE "commons_repo_features" ADD CONSTRAINT "repo_id_refs_id_f3e93f26" FOREIGN KEY ("repo_id") REFERENCES "commons_repo" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "commons_repo_languages" ADD CONSTRAINT "repo_id_refs_id_be5aa5ae" FOREIGN KEY ("repo_id") REFERENCES "commons_repo" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "commons_repo_subjects" ADD CONSTRAINT "repo_id_refs_id_bf4ec7b9" FOREIGN KEY ("repo_id") REFERENCES "commons_repo" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "commons_oer_accessibility" (
    "id" serial NOT NULL PRIMARY KEY,
    "oer_id" integer NOT NULL,
    "accessibilityentry_id" integer NOT NULL REFERENCES "commons_accessibilityentry" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("oer_id", "accessibilityentry_id")
)
;
CREATE TABLE "commons_oer_documents" (
    "id" serial NOT NULL PRIMARY KEY,
    "oer_id" integer NOT NULL,
    "document_id" integer NOT NULL REFERENCES "documents_document" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("oer_id", "document_id")
)
;
CREATE TABLE "commons_oer_oers" (
    "id" serial NOT NULL PRIMARY KEY,
    "from_oer_id" integer NOT NULL,
    "to_oer_id" integer NOT NULL,
    UNIQUE ("from_oer_id", "to_oer_id")
)
;
CREATE TABLE "commons_oer_languages" (
    "id" serial NOT NULL PRIMARY KEY,
    "oer_id" integer NOT NULL,
    "language_id" varchar(5) NOT NULL REFERENCES "commons_language" ("code") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("oer_id", "language_id")
)
;
CREATE TABLE "commons_oer_subjects" (
    "id" serial NOT NULL PRIMARY KEY,
    "oer_id" integer NOT NULL,
    "subjectnode_id" integer NOT NULL REFERENCES "commons_subjectnode" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("oer_id", "subjectnode_id")
)
;
CREATE TABLE "commons_oer_levels" (
    "id" serial NOT NULL PRIMARY KEY,
    "oer_id" integer NOT NULL,
    "levelnode_id" integer NOT NULL REFERENCES "commons_levelnode" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("oer_id", "levelnode_id")
)
;
CREATE TABLE "commons_oer_media" (
    "id" serial NOT NULL PRIMARY KEY,
    "oer_id" integer NOT NULL,
    "mediaentry_id" integer NOT NULL REFERENCES "commons_mediaentry" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("oer_id", "mediaentry_id")
)
;
CREATE TABLE "commons_oer" (
    "id" serial NOT NULL PRIMARY KEY,
    "slug" varchar(50) NOT NULL UNIQUE,
    "title" varchar(200) NOT NULL,
    "description" text,
    "oer_type" integer NOT NULL,
    "source_type" integer NOT NULL,
    "source_id" integer REFERENCES "commons_repo" ("id") DEFERRABLE INITIALLY DEFERRED,
    "url" varchar(64),
    "reference" text,
    "material_id" integer REFERENCES "commons_materialentry" ("id") DEFERRABLE INITIALLY DEFERRED,
    "license_id" integer REFERENCES "commons_licensenode" ("id") DEFERRABLE INITIALLY DEFERRED,
    "project_id" integer NOT NULL REFERENCES "commons_project" ("id") DEFERRABLE INITIALLY DEFERRED,
    "state" integer,
    "created" timestamp with time zone NOT NULL,
    "modified" timestamp with time zone NOT NULL,
    "creator_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "editor_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
ALTER TABLE "commons_oer_accessibility" ADD CONSTRAINT "oer_id_refs_id_6b1109d7" FOREIGN KEY ("oer_id") REFERENCES "commons_oer" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "commons_oer_documents" ADD CONSTRAINT "oer_id_refs_id_0c5faf8b" FOREIGN KEY ("oer_id") REFERENCES "commons_oer" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "commons_oer_oers" ADD CONSTRAINT "from_oer_id_refs_id_09361874" FOREIGN KEY ("from_oer_id") REFERENCES "commons_oer" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "commons_oer_oers" ADD CONSTRAINT "to_oer_id_refs_id_09361874" FOREIGN KEY ("to_oer_id") REFERENCES "commons_oer" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "commons_oer_languages" ADD CONSTRAINT "oer_id_refs_id_a1f1192a" FOREIGN KEY ("oer_id") REFERENCES "commons_oer" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "commons_oer_subjects" ADD CONSTRAINT "oer_id_refs_id_cfe3da6d" FOREIGN KEY ("oer_id") REFERENCES "commons_oer" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "commons_oer_levels" ADD CONSTRAINT "oer_id_refs_id_4d219eda" FOREIGN KEY ("oer_id") REFERENCES "commons_oer" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "commons_oer_media" ADD CONSTRAINT "oer_id_refs_id_87e86869" FOREIGN KEY ("oer_id") REFERENCES "commons_oer" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "commons_oermetadata" (
    "id" serial NOT NULL PRIMARY KEY,
    "oer_id" integer NOT NULL REFERENCES "commons_oer" ("id") DEFERRABLE INITIALLY DEFERRED,
    "metadata_type_id" integer NOT NULL REFERENCES "metadata_metadatatype" ("id") DEFERRABLE INITIALLY DEFERRED,
    "value" varchar(255),
    UNIQUE ("oer_id", "metadata_type_id", "value")
)
;
CREATE TABLE "commons_learningpath_levels" (
    "id" serial NOT NULL PRIMARY KEY,
    "learningpath_id" integer NOT NULL,
    "levelnode_id" integer NOT NULL REFERENCES "commons_levelnode" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("learningpath_id", "levelnode_id")
)
;
CREATE TABLE "commons_learningpath_subjects" (
    "id" serial NOT NULL PRIMARY KEY,
    "learningpath_id" integer NOT NULL,
    "subjectnode_id" integer NOT NULL REFERENCES "commons_subjectnode" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("learningpath_id", "subjectnode_id")
)
;
CREATE TABLE "commons_learningpath" (
    "id" serial NOT NULL PRIMARY KEY,
    "slug" varchar(50) NOT NULL UNIQUE,
    "title" varchar(200) NOT NULL,
    "path_type" integer NOT NULL,
    "short" text NOT NULL,
    "long" text NOT NULL,
    "project_id" integer NOT NULL REFERENCES "commons_project" ("id") DEFERRABLE INITIALLY DEFERRED,
    "state" integer,
    "created" timestamp with time zone NOT NULL,
    "modified" timestamp with time zone NOT NULL,
    "creator_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "editor_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
ALTER TABLE "commons_learningpath_levels" ADD CONSTRAINT "learningpath_id_refs_id_534d2d5d" FOREIGN KEY ("learningpath_id") REFERENCES "commons_learningpath" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "commons_learningpath_subjects" ADD CONSTRAINT "learningpath_id_refs_id_09cb2724" FOREIGN KEY ("learningpath_id") REFERENCES "commons_learningpath" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "commons_pathnode" (
    "id" serial NOT NULL PRIMARY KEY,
    "path_id" integer NOT NULL REFERENCES "commons_learningpath" ("id") DEFERRABLE INITIALLY DEFERRED,
    "label" text NOT NULL,
    "oer_id" integer NOT NULL REFERENCES "commons_oer" ("id") DEFERRABLE INITIALLY DEFERRED,
    "created" timestamp with time zone NOT NULL,
    "modified" timestamp with time zone NOT NULL,
    "creator_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "editor_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "commons_pathedge" (
    "id" serial NOT NULL PRIMARY KEY,
    "parent_id" integer NOT NULL REFERENCES "commons_pathnode" ("id") DEFERRABLE INITIALLY DEFERRED,
    "child_id" integer NOT NULL REFERENCES "commons_pathnode" ("id") DEFERRABLE INITIALLY DEFERRED,
    "label" text NOT NULL,
    "content" text NOT NULL,
    "created" timestamp with time zone NOT NULL,
    "modified" timestamp with time zone NOT NULL,
    "creator_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "editor_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE INDEX "commons_materialentry_name_like" ON "commons_materialentry" ("name" varchar_pattern_ops);
CREATE INDEX "commons_mediaentry_name_like" ON "commons_mediaentry" ("name" varchar_pattern_ops);
CREATE INDEX "commons_accessibilityentry_name_like" ON "commons_accessibilityentry" ("name" varchar_pattern_ops);
CREATE INDEX "commons_levelnode_name_like" ON "commons_levelnode" ("name" varchar_pattern_ops);
CREATE INDEX "commons_levelnode_parent_id" ON "commons_levelnode" ("parent_id");
CREATE INDEX "commons_levelnode_lft" ON "commons_levelnode" ("lft");
CREATE INDEX "commons_levelnode_rght" ON "commons_levelnode" ("rght");
CREATE INDEX "commons_levelnode_tree_id" ON "commons_levelnode" ("tree_id");
CREATE INDEX "commons_levelnode_level" ON "commons_levelnode" ("level");
CREATE INDEX "commons_subjectnode_name_like" ON "commons_subjectnode" ("name" varchar_pattern_ops);
CREATE INDEX "commons_subjectnode_parent_id" ON "commons_subjectnode" ("parent_id");
CREATE INDEX "commons_subjectnode_lft" ON "commons_subjectnode" ("lft");
CREATE INDEX "commons_subjectnode_rght" ON "commons_subjectnode" ("rght");
CREATE INDEX "commons_subjectnode_tree_id" ON "commons_subjectnode" ("tree_id");
CREATE INDEX "commons_subjectnode_level" ON "commons_subjectnode" ("level");
CREATE INDEX "commons_licensenode_name_like" ON "commons_licensenode" ("name" varchar_pattern_ops);
CREATE INDEX "commons_licensenode_parent_id" ON "commons_licensenode" ("parent_id");
CREATE INDEX "commons_licensenode_lft" ON "commons_licensenode" ("lft");
CREATE INDEX "commons_licensenode_rght" ON "commons_licensenode" ("rght");
CREATE INDEX "commons_licensenode_tree_id" ON "commons_licensenode" ("tree_id");
CREATE INDEX "commons_licensenode_level" ON "commons_licensenode" ("level");
CREATE INDEX "commons_edulevelentry_name_like" ON "commons_edulevelentry" ("name" varchar_pattern_ops);
CREATE INDEX "commons_prostatusnode_name_like" ON "commons_prostatusnode" ("name" varchar_pattern_ops);
CREATE INDEX "commons_prostatusnode_parent_id" ON "commons_prostatusnode" ("parent_id");
CREATE INDEX "commons_prostatusnode_lft" ON "commons_prostatusnode" ("lft");
CREATE INDEX "commons_prostatusnode_rght" ON "commons_prostatusnode" ("rght");
CREATE INDEX "commons_prostatusnode_tree_id" ON "commons_prostatusnode" ("tree_id");
CREATE INDEX "commons_prostatusnode_level" ON "commons_prostatusnode" ("level");
CREATE INDEX "commons_edufieldentry_name_like" ON "commons_edufieldentry" ("name" varchar_pattern_ops);
CREATE INDEX "commons_profieldentry_name_like" ON "commons_profieldentry" ("name" varchar_pattern_ops);
CREATE INDEX "commons_networkentry_name_like" ON "commons_networkentry" ("name" varchar_pattern_ops);
CREATE INDEX "commons_language_code_like" ON "commons_language" ("code" varchar_pattern_ops);
CREATE INDEX "commons_countryentry_code_like" ON "commons_countryentry" ("code" varchar_pattern_ops);
CREATE INDEX "commons_userprofile_languages_userprofile_id" ON "commons_userprofile_languages" ("userprofile_id");
CREATE INDEX "commons_userprofile_languages_language_id" ON "commons_userprofile_languages" ("language_id");
CREATE INDEX "commons_userprofile_languages_language_id_like" ON "commons_userprofile_languages" ("language_id" varchar_pattern_ops);
CREATE INDEX "commons_userprofile_subjects_userprofile_id" ON "commons_userprofile_subjects" ("userprofile_id");
CREATE INDEX "commons_userprofile_subjects_subjectnode_id" ON "commons_userprofile_subjects" ("subjectnode_id");
CREATE INDEX "commons_userprofile_networks_userprofile_id" ON "commons_userprofile_networks" ("userprofile_id");
CREATE INDEX "commons_userprofile_networks_networkentry_id" ON "commons_userprofile_networks" ("networkentry_id");
CREATE INDEX "commons_userprofile_country_id" ON "commons_userprofile" ("country_id");
CREATE INDEX "commons_userprofile_country_id_like" ON "commons_userprofile" ("country_id" varchar_pattern_ops);
CREATE INDEX "commons_userprofile_edu_level_id" ON "commons_userprofile" ("edu_level_id");
CREATE INDEX "commons_userprofile_pro_status_id" ON "commons_userprofile" ("pro_status_id");
CREATE INDEX "commons_userprofile_edu_field_id" ON "commons_userprofile" ("edu_field_id");
CREATE INDEX "commons_userprofile_pro_field_id" ON "commons_userprofile" ("pro_field_id");
CREATE INDEX "commons_subject_code_like" ON "commons_subject" ("code" varchar_pattern_ops);
CREATE INDEX "commons_projtype_name_like" ON "commons_projtype" ("name" varchar_pattern_ops);
CREATE INDEX "commons_project_slug_like" ON "commons_project" ("slug" varchar_pattern_ops);
CREATE INDEX "commons_project_proj_type_id" ON "commons_project" ("proj_type_id");
CREATE INDEX "commons_project_creator_id" ON "commons_project" ("creator_id");
CREATE INDEX "commons_project_editor_id" ON "commons_project" ("editor_id");
CREATE INDEX "commons_projectmember_project_id" ON "commons_projectmember" ("project_id");
CREATE INDEX "commons_projectmember_user_id" ON "commons_projectmember" ("user_id");
CREATE INDEX "commons_projectmember_editor_id" ON "commons_projectmember" ("editor_id");
CREATE INDEX "commons_repotype_name_like" ON "commons_repotype" ("name" varchar_pattern_ops);
CREATE INDEX "commons_repo_features_repo_id" ON "commons_repo_features" ("repo_id");
CREATE INDEX "commons_repo_features_repofeature_id" ON "commons_repo_features" ("repofeature_id");
CREATE INDEX "commons_repo_languages_repo_id" ON "commons_repo_languages" ("repo_id");
CREATE INDEX "commons_repo_languages_language_id" ON "commons_repo_languages" ("language_id");
CREATE INDEX "commons_repo_languages_language_id_like" ON "commons_repo_languages" ("language_id" varchar_pattern_ops);
CREATE INDEX "commons_repo_subjects_repo_id" ON "commons_repo_subjects" ("repo_id");
CREATE INDEX "commons_repo_subjects_subjectnode_id" ON "commons_repo_subjects" ("subjectnode_id");
CREATE INDEX "commons_repo_name" ON "commons_repo" ("name");
CREATE INDEX "commons_repo_name_like" ON "commons_repo" ("name" varchar_pattern_ops);
CREATE INDEX "commons_repo_slug_like" ON "commons_repo" ("slug" varchar_pattern_ops);
CREATE INDEX "commons_repo_repo_type_id" ON "commons_repo" ("repo_type_id");
CREATE INDEX "commons_repo_creator_id" ON "commons_repo" ("creator_id");
CREATE INDEX "commons_repo_editor_id" ON "commons_repo" ("editor_id");
CREATE INDEX "commons_oer_accessibility_oer_id" ON "commons_oer_accessibility" ("oer_id");
CREATE INDEX "commons_oer_accessibility_accessibilityentry_id" ON "commons_oer_accessibility" ("accessibilityentry_id");
CREATE INDEX "commons_oer_documents_oer_id" ON "commons_oer_documents" ("oer_id");
CREATE INDEX "commons_oer_documents_document_id" ON "commons_oer_documents" ("document_id");
CREATE INDEX "commons_oer_oers_from_oer_id" ON "commons_oer_oers" ("from_oer_id");
CREATE INDEX "commons_oer_oers_to_oer_id" ON "commons_oer_oers" ("to_oer_id");
CREATE INDEX "commons_oer_languages_oer_id" ON "commons_oer_languages" ("oer_id");
CREATE INDEX "commons_oer_languages_language_id" ON "commons_oer_languages" ("language_id");
CREATE INDEX "commons_oer_languages_language_id_like" ON "commons_oer_languages" ("language_id" varchar_pattern_ops);
CREATE INDEX "commons_oer_subjects_oer_id" ON "commons_oer_subjects" ("oer_id");
CREATE INDEX "commons_oer_subjects_subjectnode_id" ON "commons_oer_subjects" ("subjectnode_id");
CREATE INDEX "commons_oer_levels_oer_id" ON "commons_oer_levels" ("oer_id");
CREATE INDEX "commons_oer_levels_levelnode_id" ON "commons_oer_levels" ("levelnode_id");
CREATE INDEX "commons_oer_media_oer_id" ON "commons_oer_media" ("oer_id");
CREATE INDEX "commons_oer_media_mediaentry_id" ON "commons_oer_media" ("mediaentry_id");
CREATE INDEX "commons_oer_slug_like" ON "commons_oer" ("slug" varchar_pattern_ops);
CREATE INDEX "commons_oer_title" ON "commons_oer" ("title");
CREATE INDEX "commons_oer_title_like" ON "commons_oer" ("title" varchar_pattern_ops);
CREATE INDEX "commons_oer_source_id" ON "commons_oer" ("source_id");
CREATE INDEX "commons_oer_material_id" ON "commons_oer" ("material_id");
CREATE INDEX "commons_oer_license_id" ON "commons_oer" ("license_id");
CREATE INDEX "commons_oer_project_id" ON "commons_oer" ("project_id");
CREATE INDEX "commons_oer_creator_id" ON "commons_oer" ("creator_id");
CREATE INDEX "commons_oer_editor_id" ON "commons_oer" ("editor_id");
CREATE INDEX "commons_oermetadata_oer_id" ON "commons_oermetadata" ("oer_id");
CREATE INDEX "commons_oermetadata_metadata_type_id" ON "commons_oermetadata" ("metadata_type_id");
CREATE INDEX "commons_oermetadata_value" ON "commons_oermetadata" ("value");
CREATE INDEX "commons_oermetadata_value_like" ON "commons_oermetadata" ("value" varchar_pattern_ops);
CREATE INDEX "commons_learningpath_levels_learningpath_id" ON "commons_learningpath_levels" ("learningpath_id");
CREATE INDEX "commons_learningpath_levels_levelnode_id" ON "commons_learningpath_levels" ("levelnode_id");
CREATE INDEX "commons_learningpath_subjects_learningpath_id" ON "commons_learningpath_subjects" ("learningpath_id");
CREATE INDEX "commons_learningpath_subjects_subjectnode_id" ON "commons_learningpath_subjects" ("subjectnode_id");
CREATE INDEX "commons_learningpath_slug_like" ON "commons_learningpath" ("slug" varchar_pattern_ops);
CREATE INDEX "commons_learningpath_title" ON "commons_learningpath" ("title");
CREATE INDEX "commons_learningpath_title_like" ON "commons_learningpath" ("title" varchar_pattern_ops);
CREATE INDEX "commons_learningpath_project_id" ON "commons_learningpath" ("project_id");
CREATE INDEX "commons_learningpath_creator_id" ON "commons_learningpath" ("creator_id");
CREATE INDEX "commons_learningpath_editor_id" ON "commons_learningpath" ("editor_id");
CREATE INDEX "commons_pathnode_path_id" ON "commons_pathnode" ("path_id");
CREATE INDEX "commons_pathnode_oer_id" ON "commons_pathnode" ("oer_id");
CREATE INDEX "commons_pathnode_creator_id" ON "commons_pathnode" ("creator_id");
CREATE INDEX "commons_pathnode_editor_id" ON "commons_pathnode" ("editor_id");
CREATE INDEX "commons_pathedge_parent_id" ON "commons_pathedge" ("parent_id");
CREATE INDEX "commons_pathedge_child_id" ON "commons_pathedge" ("child_id");
CREATE INDEX "commons_pathedge_creator_id" ON "commons_pathedge" ("creator_id");
CREATE INDEX "commons_pathedge_editor_id" ON "commons_pathedge" ("editor_id");

COMMIT;
