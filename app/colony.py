"""Blueprint for routes to run and access the PIE colony recognotion workflow
application.
"""

from flask import Blueprint, request, render_template, url_for

import numpy as np
import pandas as pd

from flowserv.app import flowapp

import flowserv.util as util


"""Templates for PIE colony recognition web pages."""
TEMPLATE_INPUT = 'public/upload_image.html'
TEMPLATE_RESULT = 'public/render_image.html'


bp = Blueprint('colonies', __name__, url_prefix='/app')


@bp.route('/colonies', methods=['GET'])
def pie_colonies_input():
    """Render the colonies input form."""
    return render_template(TEMPLATE_INPUT)


@bp.route('/colonies', methods=['POST'])
def pie_colonies_run():
    """Run the PIE colony recognition algorithm using the values from an input
    form that was submitted by the user.
    """
    # Ensure that at least one input file was submitted by the user. If not,
    # the input form is rendered.
    if not request.files:
        return render_template(TEMPLATE_INPUT)
    files = request.files.getlist('image')
    if not files:
        return render_template(TEMPLATE_INPUT)
    # Get input arguments for the PIE colony recognition workflow from the
    # submitted input form.
    workflow = flowapp('piesingle')
    params = workflow.parameters()
    args = dict({
        'infile': util.flask_upload(files[0]),
        'imageType': 'brightfield',
        'holeFillArea': 'inf',
        'cleanup': False,
        'maxProportion': 0.25
    })
    for key, value in request.form.items():
        if key == 'ImageType' and value == 'phasecontrast':
            args['imageType'] = 'phasecontrast'
        elif key == 'HoleFillArea':
            if value == 'inf' or value == '':
                continue
            args['holeFillArea'] = params['holeFillArea'].to_argument(value)
        elif key == 'MaxProportionExposedEdge' and value != "":
            args['cleanup'] = True
            args['maxProportion'] = params['maxProportion'].to_argument(value)
    # Run the PIE workflow.
    state = workflow.start_run(args)
    run_id = state['id']
    for obj in state['files']:
        if obj['name'] == 'data/OUT/single_im_colony_properties/image.csv':
            buf, _, _ = workflow.get_file(run_id=run_id, file_id=obj['id'])
            df = pd.read_csv(buf)
        elif obj['name'] == 'data/OUT/boundary_ims/image.jpg':
            boundary_im_url = url_for(
                'files.download_result_file',
                workflow_id='piesingle',
                run_id=run_id,
                file_id=obj['id']
            )
    return render_template(
        TEMPLATE_RESULT,
        boundary_im_url=boundary_im_url,
        url_ls=list(),
        column_names=df.columns.values,
        row_data=list(df.values.tolist()),
        zip=zip
    )
