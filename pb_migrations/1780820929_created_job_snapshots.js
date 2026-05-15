/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = new Collection({
    "createRule": "@request.auth.id != ''",
    "deleteRule": null,
    "fields": [
      {
        "autogeneratePattern": "[a-z0-9]{15}",
        "help": "",
        "hidden": false,
        "id": "text3208210256",
        "max": 15,
        "min": 15,
        "name": "id",
        "pattern": "^[a-z0-9]+$",
        "presentable": false,
        "primaryKey": true,
        "required": true,
        "system": true,
        "type": "text"
      },
      {
        "cascadeDelete": true,
        "collectionId": "pbc_2409499253",
        "help": "",
        "hidden": false,
        "id": "relation4225294584",
        "maxSelect": 1,
        "minSelect": 0,
        "name": "job",
        "presentable": false,
        "required": true,
        "system": false,
        "type": "relation"
      },
      {
        "help": "",
        "hidden": false,
        "id": "select1305942106",
        "maxSelect": 1,
        "name": "field_changed",
        "presentable": false,
        "required": true,
        "system": false,
        "type": "select",
        "values": [
          "title",
          "salary_min",
          "salary_max",
          "location",
          "remote",
          "contract_type",
          "description",
          "is_active"
        ]
      },
      {
        "autogeneratePattern": "",
        "help": "",
        "hidden": false,
        "id": "text3152253650",
        "max": 0,
        "min": 0,
        "name": "old_value",
        "pattern": "",
        "presentable": false,
        "primaryKey": false,
        "required": false,
        "system": false,
        "type": "text"
      },
      {
        "autogeneratePattern": "",
        "help": "",
        "hidden": false,
        "id": "text3856735209",
        "max": 0,
        "min": 0,
        "name": "new_value",
        "pattern": "",
        "presentable": false,
        "primaryKey": false,
        "required": false,
        "system": false,
        "type": "text"
      },
      {
        "hidden": false,
        "id": "autodate169189612",
        "name": "detected_at",
        "onCreate": true,
        "onUpdate": false,
        "presentable": false,
        "system": false,
        "type": "autodate"
      }
    ],
    "id": "pbc_1662358621",
    "indexes": [
      "CREATE INDEX idx_snapshots_job         ON job_snapshots (job)",
      "CREATE INDEX idx_snapshots_detected_at ON job_snapshots (detected_at)",
      "CREATE INDEX idx_snapshots_field       ON job_snapshots (field_changed)"
    ],
    "listRule": "@request.auth.id != ''",
    "name": "job_snapshots",
    "system": false,
    "type": "base",
    "updateRule": null,
    "viewRule": "@request.auth.id != ''"
  });

  return app.save(collection);
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_1662358621");

  return app.delete(collection);
})
