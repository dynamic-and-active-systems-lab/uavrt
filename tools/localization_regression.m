function localization_regression(outFile)
%LOCALIZATION_REGRESSION Regression harness for uavrt_bearing / uavrt_localize.
%
%   Captures the numeric output of the bearing and localization chain against the
%   example fixtures shipped in the repos, so that a refactor can be shown not to
%   change results.
%
%   USAGE (from anywhere; run via matlab -batch):
%       localization_regression
%       localization_regression('/path/to/out.txt')
%
%   HISTORY
%   Until 2026-09-01 this took a utilsSource argument ('bearing' or 'utils'),
%   because uavrt_bearing carried its own copies of the 15 shared functions that
%   also live in uavrt_localization_utils, and five had diverged. That argument
%   is gone: uavrt_bearing now consumes uavrt_localization_utils as a submodule
%   and the duplicate copies were removed, so there is exactly one copy to test.
%
%   The comparison it existed for is recorded in SOFTWARE_CONTEXT.md section 9b.
%   Reference values from that work, all of which must still hold:
%       rotation_example.csv                     197.718853
%       rotation_example_2.csv                   179.806138
%       rotation_example_2_with_ant_offset.csv   269.806138   (exactly +90.000000)
%       rotation_example_old.csv                 pre-existing failure, both before
%                                                and after; not a regression
%       localize()                               reproduces positions_example.csv
%
%   SIDE EFFECTS ARE CONTAINED
%   bearing() appends to / rewrites a bearings.csv beside its input, and localize()
%   writes a positions csv. All fixtures are therefore copied into a fresh temp
%   directory and the work happens there; the repo files are never modified.
%
%   NOT A CORRECTNESS TEST. It records what the code currently does. A changed
%   number means behaviour changed; it does not tell you which answer is right.

arguments
    outFile (1,:) char = ''
end

root = '/Users/mws22/Developer/uavrt';
if isempty(outFile)
    outFile = fullfile(root, '_baseline', 'localization.txt');
end

%% ---- Path: explicit and minimal --------------------------------------------
% restoredefaultpath so results do not depend on the saved path. The shared
% functions come from uavrt_bearing's submodule; the standalone
% uavrt_localization_utils checkout at the top of the working directory is
% deliberately NOT added, so nothing can shadow it.
oldPath = path();
cleanup = onCleanup(@() path(oldPath));
restoredefaultpath();
addpath(fullfile(root, 'uavrt_bearing'));
addpath(fullfile(root, 'uavrt_bearing', 'uavrt_localization_utils'));
addpath(fullfile(root, 'uavrt_localize'));

sharedDir = fullfile(root, 'uavrt_bearing', 'uavrt_localization_utils');
if ~isfile(fullfile(sharedDir, 'doapca.m'))
    error('localization_regression:submoduleMissing', ...
          ['Shared functions not found in %s\n' ...
           'Run: git -C %s submodule update --init --recursive'], ...
          sharedDir, fullfile(root, 'uavrt_bearing'));
end

%% ---- Sandbox --------------------------------------------------------------
work = tempname; mkdir(work);
cleanup2 = onCleanup(@() rmdir(work, 's')); %#ok<NASGU>

pulseFixtures = { 'rotation_example.csv', ...
                  'rotation_example_2.csv', ...
                  'rotation_example_2_with_ant_offset.csv', ...
                  'rotation_example_old.csv' };
for k = 1:numel(pulseFixtures)
    src = fullfile(root, 'uavrt_bearing', pulseFixtures{k});
    if isfile(src), copyfile(src, work); end
end
copyfile(fullfile(root, 'uavrt_bearing', 'bearing_example.csv'), work);

fid = fopen(outFile, 'w');
assert(fid ~= -1, 'could not open %s', outFile);
c3 = onCleanup(@() fclose(fid)); %#ok<NASGU>

emit(fid, '=== uavrt localization regression ===');
emit(fid, 'shared funcs : uavrt_bearing/uavrt_localization_utils (submodule)');
emit(fid, 'matlab       : %s', version);
emit(fid, 'which doapca : %s', relpath(which('doapca'), root));
emit(fid, 'which readbearingcsv : %s', relpath(which('readbearingcsv'), root));
emit(fid, 'which readpulsecsv   : %s', relpath(which('readpulsecsv'), root));
emit(fid, '');

%% ---- bearing() ------------------------------------------------------------
emit(fid, '--- bearing() over pulse fixtures ---');
for k = 1:numel(pulseFixtures)
    f = fullfile(work, pulseFixtures{k});
    if ~isfile(f)
        emit(fid, '%-42s SKIPPED (fixture absent)', pulseFixtures{k});
        continue
    end
    % Each fixture gets its own directory so the bearings.csv side effect of one
    % cannot influence the next.
    sub = fullfile(work, sprintf('b%02d', k)); mkdir(sub);
    copyfile(f, sub);
    try
        b = bearing(fullfile(sub, pulseFixtures{k}), true);
        emit(fid, '%-42s bearing_deg = %.6f', pulseFixtures{k}, b);
    catch ME
        emit(fid, '%-42s ERROR %s | %s', pulseFixtures{k}, ME.identifier, ME.message);
    end
end
emit(fid, '');

%% ---- localize() -----------------------------------------------------------
emit(fid, '--- localize() over bearing_example.csv ---');
sub = fullfile(work, 'loc'); mkdir(sub);
copyfile(fullfile(work, 'bearing_example.csv'), sub);
bf = fullfile(sub, 'bearing_example.csv');
try
    r = localize(bf);
    emit(fid, 'localize() returned %d', r);
    posFile = '';
    d = dir(fullfile(sub, '*.csv'));
    for k = 1:numel(d)
        if ~strcmp(d(k).name, 'bearing_example.csv'), posFile = fullfile(sub, d(k).name); end
    end
    if isempty(posFile)
        emit(fid, 'no positions file produced');
    else
        emit(fid, 'positions file: %s', posFileName(posFile));
        txt = strsplit(strtrim(fileread(posFile)), newline);
        for k = 1:numel(txt), emit(fid, '  %s', strtrim(txt{k})); end
    end
catch ME
    emit(fid, 'ERROR %s | %s', ME.identifier, ME.message);
end

emit(fid, '');
emit(fid, '=== end ===');
fprintf('wrote %s\n', outFile);
end

% --------------------------------------------------------------------------
function emit(fid, fmt, varargin)
line = sprintf(fmt, varargin{:});
fprintf(fid, '%s\n', line);
fprintf('%s\n', line);
end

function s = relpath(p, root)
if isempty(p), s = '(not found)'; return; end
s = strrep(p, [root filesep], '');
end

function s = posFileName(p)
[~, n, e] = fileparts(p); s = [n e];
end
