-- Create the maze_stages table
CREATE TABLE IF NOT EXISTS maze_stages (
    stage_id SERIAL PRIMARY KEY,
    stage_number INTEGER UNIQUE NOT NULL,
    layout TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    start_x INTEGER NOT NULL,
    start_y INTEGER NOT NULL,
    end_x INTEGER NOT NULL,
    end_y INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create game_statistics table for analytics
CREATE TABLE IF NOT EXISTS game_statistics (
    stat_id SERIAL PRIMARY KEY,
    player_id VARCHAR(100),
    stage_number INTEGER,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_taken INTEGER, -- in seconds
    moves_count INTEGER
);

-- Insert 10 maze stages
-- Layout format: '#' = wall, '.' = path, 'S' = start, 'E' = end

-- Stage 1: Simple introductory maze
INSERT INTO maze_stages (stage_number, layout, width, height, start_x, start_y, end_x, end_y) VALUES
(1, 
'###########
#........S#
#.########.
#.........#
########.##
#........##
#.#########
#........E#
###########',
11, 9, 1, 1, 9, 7);

-- Stage 2: Slightly more complex
INSERT INTO maze_stages (stage_number, layout, width, height, start_x, start_y, end_x, end_y) VALUES
(2,
'#############
#S..........#
##.########.#
#..#......#.#
#.##.####.#.#
#....#....#.#
######.######
#..........E#
#############',
13, 9, 1, 1, 11, 7);

-- Stage 3: With dead ends
INSERT INTO maze_stages (stage_number, layout, width, height, start_x, start_y, end_x, end_y) VALUES
(3,
'###############
#S............#
#.###########.#
#.#.........#.#
#.#.#######.#.#
#...#.....#...#
#####.###.###.#
#......#......#
#.#############
#...........E.#
###############',
15, 11, 1, 1, 12, 9);

-- Stage 4: Spiral pattern
INSERT INTO maze_stages (stage_number, layout, width, height, start_x, start_y, end_x, end_y) VALUES
(4,
'###############
#S############.#
#.#..........#.#
#.#.########.#.#
#.#.#......#.#.#
#.#.#.####.#.#.#
#.#.#....#...#.#
#.#.######.###.#
#.............E#
###############',
15, 10, 1, 1, 14, 8);

-- Stage 5: Multiple paths
INSERT INTO maze_stages (stage_number, layout, width, height, start_x, start_y, end_x, end_y) VALUES
(5,
'#################
#S..#...........#
#.#.#.#########.#
#.#...#.......#.#
#.#####.#####.#.#
#.......#...#.#.#
#########.#.#.#.#
#.........#...#.#
#.#############.#
#.............E.#
#################',
17, 11, 1, 1, 14, 9);

-- Stage 6: Zigzag maze
INSERT INTO maze_stages (stage_number, layout, width, height, start_x, start_y, end_x, end_y) VALUES
(6,
'###################
#S................#
##.##############.#
#...............#.#
#.##############.##
#.#.............#.#
#.#.############.#.
#...#...........#..
###.#.###########.#
#.................E
###################',
19, 11, 1, 1, 17, 9);

-- Stage 7: Cross pattern
INSERT INTO maze_stages (stage_number, layout, width, height, start_x, start_y, end_x, end_y) VALUES
(7,
'###################
#S.......#........#
#.#####.###.#####.#
#.#...#.....#...#.#
#.#.#.#######.#.#.#
#...#.........#...#
###.###########.###
#.#.....#.....#.#.#
#.#####.#.#####.#.#
#.......#.........E
###################',
19, 11, 1, 1, 17, 9);

-- Stage 8: Complex corridors
INSERT INTO maze_stages (stage_number, layout, width, height, start_x, start_y, end_x, end_y) VALUES
(8,
'#####################
#S..................#
#.#################.#
#.#...............#.#
#.#.#############.#.#
#...#...........#...#
#####.#########.#####
#.....#.......#.....#
#.#####.#####.#####.#
#.#.....#...#.....#.#
#.#.#####.#.#####.#.#
#.........#.........E
#####################',
21, 13, 1, 1, 19, 11);

-- Stage 9: Challenging layout
INSERT INTO maze_stages (stage_number, layout, width, height, start_x, start_y, end_x, end_y) VALUES
(9,
'#######################
#S....................#
#.###################.#
#.#.................#.#
#.#.###############.#.#
#...#.............#...#
#####.###########.#####
#.....#.........#.....#
#.#####.#######.#####.#
#.#.....#.....#.....#.#
#.#.#####.###.#####.#.#
#.#.......#.#.......#.#
#.#########.#########.#
#.....................E
#######################',
23, 15, 1, 1, 21, 13);

-- Stage 10: Final challenge
INSERT INTO maze_stages (stage_number, layout, width, height, start_x, start_y, end_x, end_y) VALUES
(10,
'#########################
#S......................#
#.#####################.#
#.#...................#.#
#.#.#################.#.#
#.#.#...............#.#.#
#.#.#.#############.#.#.#
#.#.#.#...........#.#.#.#
#.#.#.#.#########.#.#.#.#
#.#.#.#.#.......#.#.#.#.#
#.#.#.#.#.#####.#.#.#.#.#
#.#...#...#...#...#...#.#
#.#########.#.#########.#
#...........#...........#
#.#####################.#
#.......................E
#########################',
25, 17, 1, 1, 23, 15);
