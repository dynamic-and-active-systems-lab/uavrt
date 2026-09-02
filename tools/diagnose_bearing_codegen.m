function diagnose_bearing_codegen()
%DIAGNOSE_BEARING_CODEGEN Capture why bearing codegen fails, as plain text.
%
%   Run:
%     matlab -batch "addpath('/Users/mws22/Developer/uavrt/tools'); diagnose_bearing_codegen"
%
%   Writes _baseline/codegen_diagnosis.txt. Reports where every dependency of
%   bearing.m resolves, whether bearing() runs interpreted, and the full text of
%   any codegen error including its stack, which the .mat report does not expose
%   outside MATLAB.

root    = '/Users/mws22/Developer/uavrt';
repo    = fullfile(root, 'uavrt_bearing');
outFile = fullfile(root, '_baseline', 'codegen_diagnosis.txt');

fid = fopen(outFile, 'w');
c = onCleanup(@() fclose(fid));
say = @(varargin) emit(fid, varargin{:});

say('=== bearing codegen diagnosis ===');
say('matlab : %s', version);
say('repo   : %s', repo);
say('');

%% Path exactly as bearing_codegen_script sets it up
oldPath = path(); c2 = onCleanup(@() path(oldPath)); %#ok<NASGU>
restoredefaultpath();
addpath(repo);
addpath(fullfile(repo, 'uavrt_localization_utils'));
addpath(fullfile(repo, 'matlab-coder-utils', 'c-udp'));
cd(repo);

%% Where does everything resolve?
say('--- dependency resolution ---');
deps = { 'bearing','readpulsecsvtable','transmittingFilter','writeToBearingFile', ...
         'doapca','readpulsecsv','readbearingcsv','PulseStruct','CommandStruct', ...
         'EulerAngleStruct','PositionStruct','cleancsv','countlines', ...
         'gettextfilelinelocs','latlon2eastnorth','localizefrombearings', ...
         'vincentydistance','vincentyendpoint' };
missing = {};
for k = 1:numel(deps)
    w = which(deps{k});
    if isempty(w)
        say('  %-22s *** NOT FOUND ***', deps{k});
        missing{end+1} = deps{k}; %#ok<AGROW>
    else
        say('  %-22s %s', deps{k}, strrep(w, [root filesep], ''));
    end
end
say('');

%% Anything bearing.m calls that we did not list?
say('--- matlab.codetools.requiredFilesAndProducts(bearing.m) ---');
try
    [files, products] = matlab.codetools.requiredFilesAndProducts('bearing.m');
    for k = 1:numel(files)
        say('  %s', strrep(files{k}, [root filesep], ''));
    end
    say('  products: %s', strjoin({products.Name}, ', '));
catch ME
    say('  FAILED: %s | %s', ME.identifier, ME.message);
end
say('');

%% Does it run interpreted at all?
say('--- interpreted run ---');
try
    work = tempname; mkdir(work);
    copyfile(fullfile(repo, 'rotation_example.csv'), work);
    b = bearing(fullfile(work, 'rotation_example.csv'), true);
    say('  bearing() = %.6f  (expected 197.718853)', b);
    rmdir(work, 's');
catch ME
    say('  ERROR %s | %s', ME.identifier, ME.message);
    for k = 1:numel(ME.stack)
        say('    at %s line %d', ME.stack(k).name, ME.stack(k).line);
    end
end
say('');

%% Codegen, with the full error text
say('--- codegen ---');
cfg = coder.config('exe','ecoder',true);
cfg.HardwareImplementation.ProdEqTarget = false;
cfg.TargetLang           = 'C++';
cfg.GenCodeOnly          = true;
cfg.GenerateExampleMain  = 'DoNotGenerate';
cfg.GenerateMakefile     = false;
cfg.GenerateReport       = true;
cfg.MaxIdLength          = 1024;
cfg.ReportPotentialDifferences = false;
cfg.TargetLangStandard   = 'C++11 (ISO)';
cfg.RuntimeChecks        = true;
ARGS = {coder.typeof('X',[1 Inf],[0 1])};
% Do NOT wrap this in evalc. MATLAB Coder writes its diagnostics straight to the
% console and leaves ME.message empty; evalc captures that text into a variable
% and then discards it when codegen throws, which loses the only useful output.
% Let it print, and capture the console at the shell:
%   matlab -batch "..." 2>&1 | tee codegen_console.txt
say('  (Coder diagnostics print below, outside this file - see the tee''d console)');
say('');
try
    codegen('-config', cfg, 'bearing', '-args', ARGS);
    say('  codegen SUCCEEDED');
catch ME
    say('  identifier : %s', ME.identifier);
    if ~isempty(ME.message)
        say('  message    : %s', ME.message);
    end
    for k = 1:numel(ME.cause)
        say('  cause %d    : %s | %s', k, ME.cause{k}.identifier, ME.cause{k}.message);
    end
end

say('');
say('=== end ===');
fprintf('wrote %s\n', outFile);
end

function emit(fid, fmt, varargin)
line = sprintf(fmt, varargin{:});
fprintf(fid, '%s\n', line);
fprintf('%s\n', line);
end
