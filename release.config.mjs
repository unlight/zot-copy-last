import { writerOpts } from 'changelog-sentence-case';

/**
 * @type {import('semantic-release').GlobalConfig}
 */

export default {
  branches: ['master'],
  plugins: [
    [
      '@semantic-release/commit-analyzer',
      {
        preset: 'conventionalcommits',
      },
    ],
    [
      '@semantic-release/release-notes-generator',
      {
        preset: 'conventionalcommits',
        writerOpts,
      },
    ],
    '@semantic-release/changelog',
    [
      '@semantic-release/exec',
      {
        // prepare runs before the release commit and tag, so both carry the
        // version written into the manifest and the extension constant.
        prepareCmd: 'python3 sync_version.py ${nextRelease.version}',
      },
    ],
    // No @semantic-release/npm: nothing is published. The extension installs
    // from a git checkout, so a release is the tag, the GitHub release and the
    // changelog commit. There is no package.json to bump either.
    [
      '@semantic-release/git',
      {
        assets: ['CHANGELOG.md', 'extension.json', 'copy.py'],
      },
    ],
    [
      '@semantic-release/github',
      {
        // A fresh repository has no labels, and the plugin creates the failure
        // issue with 'semantic-release' by default, which GitHub rejects (422).
        labels: false,
      },
    ],
  ],
};
