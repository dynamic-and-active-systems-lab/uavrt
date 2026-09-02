function probe_table_types()
%PROBE_TABLE_TYPES Report the actual column types readpulsecsvtable produces.
%
%   Needed because Coder requires pulses/commands to hold ONE type on every
%   execution path, so the struct initialisers at readpulsecsvtable.m:22-23 must
%   become empty tables declared with the same VariableTypes as the real
%   assignments. Guessing those types would reintroduce the same class of bug,
%   so this measures them.
%
%   matlab -batch "addpath('/Users/mws22/Developer/uavrt/tools'); probe_table_types"

root = '/Users/mws22/Developer/uavrt';
repo = fullfile(root, 'uavrt_bearing');
oldPath = path(); c = onCleanup(@() path(oldPath)); %#ok<NASGU>
restoredefaultpath();
addpath(repo, fullfile(repo,'uavrt_localization_utils'));
cd(repo);

work = tempname; mkdir(work);
copyfile(fullfile(repo,'rotation_example.csv'), work);
[pulses, commands] = readpulsecsvtable(fullfile(work,'rotation_example.csv'));
rmdir(work,'s');

report(fullfile(root,'_baseline','table_types.txt'), pulses, commands);
end

function report(outFile, pulses, commands)
fid = fopen(outFile,'w'); c = onCleanup(@() fclose(fid)); %#ok<NASGU>
emit(fid, '=== readpulsecsvtable output types ===');
dump(fid, 'pulses',   pulses);
dump(fid, 'commands', commands);
emit(fid, '');
emit(fid, '--- ready-to-paste VariableTypes ---');
pasteable(fid, 'pulses',   pulses);
pasteable(fid, 'commands', commands);
fprintf('wrote %s\n', outFile);
end

function dump(fid, name, T)
emit(fid, '');
emit(fid, '%s: %s, size %dx%d', name, class(T), size(T,1), size(T,2));
if ~istable(T), emit(fid, '  NOT A TABLE'); return; end
n = T.Properties.VariableNames;
for k = 1:numel(n)
    v = T.(n{k});
    emit(fid, '  %-16s %-10s size %dx%d', n{k}, class(v), size(v,1), size(v,2));
end
end

function pasteable(fid, name, T)
if ~istable(T), return; end
n = T.Properties.VariableNames;
t = cellfun(@(v) class(T.(v)), n, 'UniformOutput', false);
emit(fid, '');
emit(fid, '%sVariableNames = {%s};', name, strjoin(cellfun(@(x) ['''' x ''''], n, 'UniformOutput', false), ','));
emit(fid, '%sVariableTypes = {%s};', name, strjoin(cellfun(@(x) ['''' x ''''], t, 'UniformOutput', false), ','));
end

function emit(fid, fmt, varargin)
line = sprintf(fmt, varargin{:});
fprintf(fid, '%s\n', line); fprintf('%s\n', line);
end
