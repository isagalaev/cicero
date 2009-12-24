BEGIN;

ALTER TABLE "cicero_article" ADD COLUMN "votes_up" integer CHECK ("votes_up" >= 0);
ALTER TABLE "cicero_article" ADD COLUMN "votes_down" integer CHECK ("votes_down" >= 0);
UPDATE "cicero_article" SET "votes_up" = 0, "votes_down" = 0;
ALTER TABLE "cicero_article" ALTER COLUMN "votes_up" SET NOT NULL;
ALTER TABLE "cicero_article" ALTER COLUMN "votes_down" SET NOT NULL;

CREATE TABLE "cicero_vote" (
    "id" serial NOT NULL PRIMARY KEY,
    "profile_id" integer NOT NULL REFERENCES "cicero_profile" ("user_id") DEFERRABLE INITIALLY DEFERRED,
    "article_id" integer NOT NULL REFERENCES "cicero_article" ("id") DEFERRABLE INITIALLY DEFERRED,
    "value" varchar(10) NOT NULL,
    UNIQUE ("profile_id", "article_id")
);
CREATE INDEX "cicero_vote_profile_id" ON "cicero_vote" ("profile_id");
CREATE INDEX "cicero_vote_article_id" ON "cicero_vote" ("article_id");

COMMIT;
