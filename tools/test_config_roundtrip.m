function test_config_roundtrip()
%TEST_CONFIG_ROUNDTRIP Verify DetectorConfig write/read symmetry.
%
%   Confirms the 2026-09-01 repair of detectorsetting2configstr.m: a config
%   written by DetectorConfig.writeToFile must read back through
%   DetectorConfig.setFromFile with every property preserved.
%
%   Run from the uavrt_detection repo directory:
%       >> addpath('/Users/mws22/Developer/uavrt/tools')
%       >> test_config_roundtrip
%
%   Before the repair this failed immediately: writeToFile errored with
%   "Not enough input arguments" because the function declared 20 parameters
%   and the caller passed 17.

srcConfig = '/Users/mws22/Developer/uavrt/_baseline/detector.2.baseline.config';
tmpConfig = [tempname, '.config'];

fprintf('--- DetectorConfig round-trip test ---\n');

% 1. Read the known-good config written by MavlinkTagController2's format.
a = DetectorConfig();
a = a.setFromFile(srcConfig, -1);
fprintf('read source config      : OK  (ID=%d, Fs=%g, tag=%.6f MHz)\n', ...
        a.ID, a.Fs, a.tagFreqMHz);

% 2. Write it back out through the MATLAB writer.
a.writeToFile(tmpConfig, 'w');
fprintf('writeToFile             : OK  (%s)\n', tmpConfig);

% 3. Read the file we just wrote.
b = DetectorConfig();
b = b.setFromFile(tmpConfig, -1);
fprintf('re-read written config  : OK\n\n');

% 4. Compare every property.
props  = properties(a);
failed = {};
for i = 1:numel(props)
    p  = props{i};
    va = a.(p);
    vb = b.(p);
    if isstring(va) || ischar(va)
        same = strcmp(string(va), string(vb));
    else
        same = isequaln(va, vb) || (isnumeric(va) && isnumeric(vb) && ...
               all(abs(double(va(:)) - double(vb(:))) < 1e-6));
    end
    if same
        fprintf('  %-22s ok\n', p);
    else
        fprintf('  %-22s *** DIFFERS ***  before=%s  after=%s\n', ...
                p, mat2str(va), mat2str(vb));
        failed{end+1} = p; %#ok<AGROW>
    end
end

fprintf('\n');
if isempty(failed)
    fprintf('RESULT: PASS - all %d properties survive the round trip.\n', numel(props));
else
    fprintf('RESULT: FAIL - %d propert(ies) changed: %s\n', ...
            numel(failed), strjoin(failed, ', '));
end

delete(tmpConfig);
end
