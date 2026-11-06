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
      },
    ],
    '@semantic-release/changelog',
    // No @semantic-release/npm: nothing is published. The extension installs
    // from a git checkout, so a release is the tag, the GitHub release and the
    // changelog commit. package.json keeps its 0.0.0 and is never rewritten.
    '@semantic-release/git',
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
