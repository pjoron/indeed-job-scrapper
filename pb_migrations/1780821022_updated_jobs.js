/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_2409499253")

  // update collection data
  unmarshal({
    "indexes": [
      "CREATE UNIQUE INDEX idx_jobs_source_id ON jobs (source, source_id)",
      "CREATE INDEX idx_jobs_company ON jobs (company)",
      "CREATE INDEX idx_jobs_posted_at ON jobs (posted_at)",
      "CREATE INDEX idx_jobs_is_active ON jobs (is_active)",
      "CREATE INDEX idx_jobs_source ON jobs (source)",
      "CREATE INDEX idx_jobs_contract ON jobs (contract_type)"
    ]
  }, collection)

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_2409499253")

  // update collection data
  unmarshal({
    "indexes": [
      "CREATE UNIQUE INDEX idx_jobs_source_id ON jobs (source, source_id)",
      "CREATE INDEX idx_jobs_company     ON jobs (company)",
      "CREATE INDEX idx_jobs_posted_at   ON jobs (posted_at)",
      "CREATE INDEX idx_jobs_is_active   ON jobs (is_active)",
      "CREATE INDEX idx_jobs_source      ON jobs (source)",
      "CREATE INDEX idx_jobs_contract    ON jobs (contract_type)"
    ]
  }, collection)

  return app.save(collection)
})
