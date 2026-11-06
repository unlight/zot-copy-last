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
    // No @semantic-release/npm: nothing is published. This extension is
    // installed by cloning the repository, so a release is a git tag, a
    // GitHub release and an updated CHANGELOG.md.
    [
      '@semantic-release/git',
      {
        // package.json stays at 0.0.0 on purpose, only the changelog moves.
        assets: ['CHANGELOG.md'],
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
