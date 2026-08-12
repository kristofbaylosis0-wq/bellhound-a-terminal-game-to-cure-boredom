from rpg_world import load_world


def test_world_loads_with_major_areas_and_locations():
    world = load_world()
    major = [area for area in world.areas.values() if area.parent is None]

    assert len(major) == 8
    assert len(world.locations) >= 40
    assert world.start_location in world.locations


def test_all_location_links_resolve():
    world = load_world()
    for location in world.locations.values():
        for target in location.connections:
            assert target in world.locations, (location.id, target)


def test_major_regions_are_connected():
    world = load_world()
    reachable_areas = {world.location(world.start_location).parent_area}
    frontier = [world.start_location]
    seen = set(frontier)

    while frontier:
        current = frontier.pop()
        for neighbor in world.neighbors(current):
            if neighbor.id not in seen:
                seen.add(neighbor.id)
                frontier.append(neighbor.id)
                reachable_areas.add(neighbor.parent_area)

    assert len(reachable_areas) == len(world.areas)
