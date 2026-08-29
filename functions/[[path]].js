import worker from '../dist/server/entry.mjs';

export const onRequest = async (context) => {
  return worker.fetch(context.request, context.env, context);
};
