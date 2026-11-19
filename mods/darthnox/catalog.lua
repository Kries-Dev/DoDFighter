-- SPDX-License-Identifier: MIT
-- DoD Fighter — adds our fighters (DarthNox 61, Mathilde 63, Cod1eh 68; grunts EVS Fanboy 72, EVS Hunter 73; computer-only Ironhide 74, Urrbot 76, DSS 80), the objects their
-- moves spawn (62, 64-67, 69-71, 75, 77-79) and our stages without editing base scripts.

return function(base)
    -- Our fighters (object type 0) and the objects their frames spawn (opoint
    -- oid:, type 3 = attack/ball). IDs must not clash with the stock catalog.
    local fighters_added = {
        {id = 61, path = "mods/darthnox/darthnox.txt"},
        {id = 63, path = "mods/darthnox/mathilde.txt"},
        {id = 68, path = "mods/darthnox/cod1eh.txt"},
        -- grunts: hidden from character select like Bandit and Hunter; stage 1 uses their data for
        -- Bandit (30) and Hunter (31) themselves (stage_mode.lua SWAPS), so they stay grunts there
        {id = 72, path = "mods/darthnox/evsfan.txt", hidden = true},    -- EVS Fanboy: Bandit with the user's sprites
        {id = 73, path = "mods/darthnox/evshunt.txt", hidden = true},   -- EVS Hunter: Hunter with the user's sprites
        -- computer-only: hidden from select (stage boss / com opponent)
        {id = 74, path = "mods/darthnox/ironhide.txt", hidden = true},  -- Ironhide: Deep's data, the user's sprites, 3 specials
        {id = 76, path = "mods/darthnox/urrbot.txt", hidden = true},    -- Urrbot: Freeze's data, the user's sprites, D>A + D>J
        {id = 80, path = "mods/darthnox/dss.txt", hidden = true},       -- DSS: Jack's data, the user's sprites, double flip, DvA kicks
    }
    local spawned = {
        {id = 62, kind = 3, path = "mods/darthnox/crescent.txt"},   -- DarthNox's crescent
        {id = 64, kind = 3, path = "mods/darthnox/m_staff.txt"},    -- Mathilde's homing staff
        {id = 65, kind = 3, path = "mods/darthnox/m_tornado.txt"},  -- Mathilde's tornado
        {id = 66, kind = 3, path = "mods/darthnox/m_pole.txt"},     -- Mathilde's extending staff (visual)
        {id = 67, kind = 3, path = "mods/darthnox/m_pole_d.txt"},   -- the same, diagonal (her DJA in the air)
        {id = 69, kind = 3, path = "mods/darthnox/c_kunai.txt"},    -- Cod1eh's kunai (D>A fan)
        {id = 70, kind = 3, path = "mods/darthnox/c_smoke.txt"},    -- Cod1eh's smoke (D^J cloud, DvJ puff)
        {id = 71, kind = 3, path = "mods/darthnox/c_rope.txt"},     -- Cod1eh's rope blade (DvA, visual)
        {id = 75, kind = 3, path = "mods/darthnox/ih_wave.txt"},    -- Ironhide's wave (D>A, two per blast)
        {id = 77, kind = 3, path = "mods/darthnox/ub_ball.txt"},    -- Urrbot's ice ball (D>A, 60% faster than Freeze's)
        {id = 78, kind = 3, path = "mods/darthnox/ub_spike.txt"},   -- Urrbot's large spike (the 4th of his D>J row)
        {id = 79, kind = 3, path = "mods/darthnox/ub_column.txt"},  -- Urrbot's icicle row (D>J: Freeze's three + the large one)
    }
    -- Our stages (bg ids must not clash with the stock list; see docs/STAGES.md).
    local stages_added = {
        {id = 61, path = "mods/darthnox/bg/bridge.txt"},   -- Urban Bridge (midday)
        {id = 62, path = "mods/darthnox/bg/roof.txt"},     -- Sunset Rooftop (old town, sunset)
        {id = 63, path = "mods/darthnox/bg/roofn.txt"},    -- Rooftop at Night (stage 2-5's boss arena)
        {id = 67, path = "mods/darthnox/bg/gate.txt"},     -- Fortress Gate (stage 1-1)
        {id = 68, path = "mods/darthnox/bg/yard.txt"},     -- Barracks Yard (stage 1-2)
        {id = 64, path = "mods/darthnox/bg/cells.txt"},    -- Cell Block (stage 1-3)
        {id = 65, path = "mods/darthnox/bg/barr.txt"},     -- Barracks (stage 1-4)
        {id = 66, path = "mods/darthnox/bg/hall.txt"},     -- Throne Hall (stage 1-5's boss arena)
    }
    local load, objects, backgrounds = base.load, base.objects, base.backgrounds
    local added_fighter, added_object, added_stage = false, false, false

    function base.load()
        local fighters = load()
        if not added_fighter then
            local list = base.objects().list
            for _, fighter in ipairs(fighters_added) do
                local header = assert(engine.read_resource(fighter.path):match("<bmp_begin>(.-)<bmp_end>"))
                local name = assert(header:match("name:%s*(%S+)")):gsub("_", " ")
                local portrait = assert(header:match("head:%s*(%S+)"))
                -- record = the fighter's 0-based position in the object list
                local record
                for index, entry in ipairs(list) do
                    if entry.id == fighter.id then record = index - 1; break end
                end
                assert(record, fighter.path .. " is missing from the object list")
                fighters[#fighters + 1] = {id = fighter.id, record = record, name = name,
                    portrait = portrait, path = fighter.path, hidden = fighter.hidden or false}
            end
            added_fighter = true
        end
        return fighters
    end

    function base.objects()
        local catalog = objects()
        if not added_object then
            for _, group in ipairs({fighters_added, spawned}) do
                for _, object in ipairs(group) do
                    assert(not catalog.by_id[object.id], "mod object ID " .. object.id .. " is already in use")
                    local entry = {id = object.id, kind = object.kind or 0, path = object.path}
                    catalog.list[#catalog.list + 1] = entry
                    catalog.by_id[object.id] = entry
                end
            end
            added_object = true
        end
        return catalog
    end

    -- The stock list ends with three unused templates, and a random pick skips the
    -- last two and turns the third-last into Lee On Road. Inserting before the
    -- templates keeps that rule intact and lets Random pick our stages too.
    function base.backgrounds()
        local list = backgrounds()
        if not added_stage then
            local at = #list + 1
            for index, entry in ipairs(list) do
                if entry.path:find("/template/", 1, true) then at = index; break end
            end
            for offset, stage in ipairs(stages_added) do
                table.insert(list, at + offset - 1, {id = stage.id, path = stage.path})
            end
            added_stage = true
        end
        return list
    end

    return base
end
