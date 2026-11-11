-- SPDX-License-Identifier: MIT
-- DarthNox — adds the fighter to the versus picker without editing base scripts.

return function(base)
    local fighter_id = 61
    local fighter_path = "mods/darthnox/darthnox.txt"
    local stage_path = "mods/darthnox/bg/bridge.txt"
    local load, objects, backgrounds = base.load, base.objects, base.backgrounds
    local added_fighter, added_object, added_stage = false, false, false

    function base.load()
        local fighters = load()
        if not added_fighter then
            assert(added_object or not objects().by_id[fighter_id],
                "darthnox ID is already in use")
            local header = assert(engine.read_resource(fighter_path):match("<bmp_begin>(.-)<bmp_end>"))
            local name = assert(header:match("name:%s*(%S+)")):gsub("_", " ")
            local portrait = assert(header:match("head:%s*(%S+)"))
            fighters[#fighters + 1] = {id = fighter_id,
                record = #objects().list - (added_object and 1 or 0),
                name = name, portrait = portrait,
                path = fighter_path, hidden = false}
            added_fighter = true
        end
        return fighters
    end

    function base.objects()
        local catalog = objects()
        if not added_object then
            assert(not catalog.by_id[fighter_id], "darthnox ID is already in use")
            local entry = {id = fighter_id, kind = 0, path = fighter_path}
            catalog.list[#catalog.list + 1] = entry
            catalog.by_id[fighter_id] = entry
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
