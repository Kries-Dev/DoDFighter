-- SPDX-License-Identifier: MIT
-- DoD Fighter — adds our fighters (DarthNox 61, Mathilde 63, Cod1eh 68), the objects their
-- moves spawn (62, 64-67, 69-71) and the Urban Bridge stage without editing base scripts.

return function(base)
    -- Our fighters (object type 0) and the objects their frames spawn (opoint
    -- oid:, type 3 = attack/ball). IDs must not clash with the stock catalog.
    local fighters_added = {
        {id = 61, path = "mods/darthnox/darthnox.txt"},
        {id = 63, path = "mods/darthnox/mathilde.txt"},
        {id = 68, path = "mods/darthnox/cod1eh.txt"},
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
    }
    local stage_path = "mods/darthnox/bg/bridge.txt"
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
                    portrait = portrait, path = fighter.path, hidden = false}
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
    -- templates keeps that rule intact and lets Random pick Urban Bridge too.
    function base.backgrounds()
        local list = backgrounds()
        if not added_stage then
            local at = #list + 1
            for index, entry in ipairs(list) do
                if entry.path:find("/template/", 1, true) then at = index; break end
            end
            table.insert(list, at, {id = 61, path = stage_path})
            added_stage = true
        end
        return list
    end

    return base
end
