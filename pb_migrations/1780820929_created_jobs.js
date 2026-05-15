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
        "autogeneratePattern": "",
        "help": "",
        "hidden": false,
        "id": "text724990059",
        "max": 0,
        "min": 0,
        "name": "title",
        "pattern": "",
        "presentable": false,
        "primaryKey": false,
        "required": true,
        "system": false,
        "type": "text"
      },
      {
        "autogeneratePattern": "",
        "help": "",
        "hidden": false,
        "id": "text1337919823",
        "max": 0,
        "min": 0,
        "name": "company",
        "pattern": "",
        "presentable": false,
        "primaryKey": false,
        "required": true,
        "system": false,
        "type": "text"
      },
      {
        "autogeneratePattern": "",
        "help": "",
        "hidden": false,
        "id": "text1587448267",
        "max": 0,
        "min": 0,
        "name": "location",
        "pattern": "",
        "presentable": false,
        "primaryKey": false,
        "required": false,
        "system": false,
        "type": "text"
      },
      {
        "help": "",
        "hidden": false,
        "id": "select1521909682",
        "maxSelect": 1,
        "name": "remote",
        "presentable": false,
        "required": false,
        "system": false,
        "type": "select",
        "values": [
          "remote",
          "hybrid",
          "onsite"
        ]
      },
      {
        "help": "",
        "hidden": false,
        "id": "number1612039405",
        "max": null,
        "min": 0,
        "name": "salary_min",
        "onlyInt": false,
        "presentable": false,
        "required": false,
        "system": false,
        "type": "number"
      },
      {
        "help": "",
        "hidden": false,
        "id": "number1545141172",
        "max": null,
        "min": 0,
        "name": "salary_max",
        "onlyInt": false,
        "presentable": false,
        "required": false,
        "system": false,
        "type": "number"
      },
      {
        "autogeneratePattern": "",
        "help": "",
        "hidden": false,
        "id": "text4212326974",
        "max": 0,
        "min": 0,
        "name": "salary_currency",
        "pattern": "",
        "presentable": false,
        "primaryKey": false,
        "required": false,
        "system": false,
        "type": "text"
      },
      {
        "help": "",
        "hidden": false,
        "id": "select3836418369",
        "maxSelect": 1,
        "name": "contract_type",
        "presentable": false,
        "required": false,
        "system": false,
        "type": "select",
        "values": [
          "CDI",
          "CDD",
          "Freelance",
          "Stage",
          "Alternance",
          "Interim",
          "Autre"
        ]
      },
      {
        "help": "",
        "hidden": false,
        "id": "select1602912115",
        "maxSelect": 1,
        "name": "source",
        "presentable": false,
        "required": true,
        "system": false,
        "type": "select",
        "values": [
          "linkedin",
          "indeed",
          "wttj",
          "apec",
          "pole_emploi",
          "other"
        ]
      },
      {
        "exceptDomains": null,
        "help": "",
        "hidden": false,
        "id": "url2776776943",
        "name": "source_url",
        "onlyDomains": null,
        "presentable": false,
        "required": true,
        "system": false,
        "type": "url"
      },
      {
        "autogeneratePattern": "",
        "help": "",
        "hidden": false,
        "id": "text2503744609",
        "max": 0,
        "min": 0,
        "name": "source_id",
        "pattern": "",
        "presentable": false,
        "primaryKey": false,
        "required": true,
        "system": false,
        "type": "text"
      },
      {
        "convertURLs": false,
        "help": "",
        "hidden": false,
        "id": "editor1843675174",
        "maxSize": 0,
        "name": "description",
        "presentable": false,
        "required": false,
        "system": false,
        "type": "editor"
      },
      {
        "help": "",
        "hidden": false,
        "id": "json1874629670",
        "maxSize": 0,
        "name": "tags",
        "presentable": false,
        "required": false,
        "system": false,
        "type": "json"
      },
      {
        "help": "",
        "hidden": false,
        "id": "date4222287402",
        "max": "",
        "min": "",
        "name": "posted_at",
        "presentable": false,
        "required": false,
        "system": false,
        "type": "date"
      },
      {
        "hidden": false,
        "id": "autodate4201916886",
        "name": "scraped_at",
        "onCreate": true,
        "onUpdate": false,
        "presentable": false,
        "system": false,
        "type": "autodate"
      },
      {
        "help": "",
        "hidden": false,
        "id": "date3088861482",
        "max": "",
        "min": "",
        "name": "last_seen_at",
        "presentable": false,
        "required": false,
        "system": false,
        "type": "date"
      },
      {
        "help": "",
        "hidden": false,
        "id": "bool458715613",
        "name": "is_active",
        "presentable": false,
        "required": true,
        "system": false,
        "type": "bool"
      },
      {
        "cascadeDelete": false,
        "collectionId": "pbc_2870927540",
        "help": "",
        "hidden": false,
        "id": "relation1040690666",
        "maxSelect": 1,
        "minSelect": 0,
        "name": "scrape_run",
        "presentable": false,
        "required": false,
        "system": false,
        "type": "relation"
      }
    ],
    "id": "pbc_2409499253",
    "indexes": [
      "CREATE UNIQUE INDEX idx_jobs_source_id ON jobs (source, source_id)",
      "CREATE INDEX idx_jobs_company     ON jobs (company)",
      "CREATE INDEX idx_jobs_posted_at   ON jobs (posted_at)",
      "CREATE INDEX idx_jobs_is_active   ON jobs (is_active)",
      "CREATE INDEX idx_jobs_source      ON jobs (source)",
      "CREATE INDEX idx_jobs_contract    ON jobs (contract_type)"
    ],
    "listRule": "@request.auth.id != ''",
    "name": "jobs",
    "system": false,
    "type": "base",
    "updateRule": "@request.auth.id != ''",
    "viewRule": "@request.auth.id != ''"
  });

  return app.save(collection);
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_2409499253");

  return app.delete(collection);
})
