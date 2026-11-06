/**
 * @type {import('semantic-release').GlobalConfig}
 */
const sentenceCase = (text) => (text ? text.charAt(0).toUpperCase() + text.slice(1) : text);

// Commits stay lowercase; every rendered notes entry starts with a capital.
// writerOpts is merged over the preset's, so grouping and links stay intact.
const capitalisedSubjects = {
  finalizeContext: (context) => ({
    ...context,
    commitGroups: (context.commitGroups ?? []).map((group) => ({
      ...group,
      commits: group.commits.map((commit) => ({
        ...commit,
        subject: sentenceCase(commit.subject),
      })),
    })),
  }),
};

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
        writerOpts: capitalisedSubjects,
      },
    ],
    '@semantic-release/changelog',
    // No @semantic-release/npm: nothing is published. The extension installs
    // from a git checkout, so a release is the tag, the GitHub release and the
    // changelog commit. There is no package.json to bump either.
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
