import { useRouteError } from "react-router-dom";
// import { isRouteErrorResponse } from "react-router-dom";
import PropTypes from "prop-types";
import { Result, Button } from "antd";

function ErrorPage(props) {
  const error = useRouteError();

  // if (props.notFound || isRouteErrorResponse(error)) {
  if (props.notFound || (error.status === 404 )) {
    return (
      <Result
        status="404"
        title="404"
        subTitle="Sorry, the page you visited does not exist."
        extra={<Button href="/">Back Home</Button>}
      />
    );
  }

  if (error.status === 401) {
    return (
      <Result
        status="403"
        title="401"
        subTitle="Sorry, you must log in to view this page."
        extra={<Button href="/">Back Home</Button>}
      />
    );
  }

  if (error.status === 403) {
    return (
      <Result
        status="403"
        title="403"
        subTitle="Sorry, you are not authorized to view this page."
        extra={<Button href="/">Back Home</Button>}
      />
    );
  }

  if (error.status === 500) {
    return (
      <Result
        status="500"
        title="503"
        subTitle="Sorry, the server is temporarily unavailable."
        extra={<Button href="/">Back Home</Button>}
      />
    );
  }

  if (error.status === 503) {
    return (
      <Result
        status="500"
        title="503"
        subTitle="Sorry, the server is temporarily unavailable."
        extra={<Button href="/">Back Home</Button>}
      />
    );
  }

  if (error.status === 418) {
    return <div>🫖</div>;
  }

  return (
    <Result
      status="warning"
      title="Something went wrong."
      extra={<Button href="/">Back Home</Button>}
    />
  );
}

ErrorPage.propTypes = {
  notFound: PropTypes.bool,
};

export default ErrorPage;