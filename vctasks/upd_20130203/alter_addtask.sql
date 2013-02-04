alter table addtask_task add column "urgent_important" varchar(1) ;
update addtask_task set urgent_important='D';
alter table addtask_task alter urgent_important set NOT NULL;

CREATE TABLE "addtask_taskcategory" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(80) NOT NULL
)
;
CREATE TABLE "addtask_task_category" (
    "id" serial NOT NULL PRIMARY KEY,
    "task_id" integer NOT NULL,
    "taskcategory_id" integer NOT NULL REFERENCES "addtask_taskcategory" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("task_id", "taskcategory_id")
)
;

ALTER TABLE "addtask_task_category" ADD CONSTRAINT "task_id_refs_id_1c41b909" FOREIGN KEY ("task_id") REFERENCES "addtask_task" ("id") DEFERRABLE INITIALLY DEFERRED;

