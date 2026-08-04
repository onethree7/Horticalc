import assert from "node:assert/strict";
import test from "node:test";

import { sortFavoriteProfiles } from "../../frontend/app/profiles.js";

test("profile favorites sort first without changing order inside either group", () => {
  const profiles = [
    { filename: "a.yml", name: "A" },
    { filename: "b.yml", name: "B" },
    { filename: "c.yml", name: "C" },
    { filename: "d.yml", name: "D" },
  ];

  const sorted = sortFavoriteProfiles(profiles, ["c.yml", "a.yml"]);

  assert.deepEqual(sorted.map(({ filename }) => filename), ["a.yml", "c.yml", "b.yml", "d.yml"]);
  assert.deepEqual(profiles.map(({ filename }) => filename), ["a.yml", "b.yml", "c.yml", "d.yml"]);
});
