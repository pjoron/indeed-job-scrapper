/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_1662358621")

  // update collection data
  unmarshal({
    "indexes": [
      "CREATE INDEX idx_snapshots_job ON job_snapshots (job)",
      "CREATE INDEX idx_snapshots_detected_at ON job_snapshots (detected_at)",
      "CREATE INDEX idx_snapshots_field ON job_snapshots (field_changed)"
    ]
  }, collection)

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_1662358621")

  // update collection data
  unmarshal({
    "indexes": [
      "CREATE INDEX idx_snapshots_job         ON job_snapshots (job)",
      "CREATE INDEX idx_snapshots_detected_at ON job_snapshots (detected_at)",
      "CREATE INDEX idx_snapshots_field       ON job_snapshots (field_changed)"
    ]
  }, collection)

  return app.save(collection)
})
